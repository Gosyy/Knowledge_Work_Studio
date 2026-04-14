from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Lock
from uuid import uuid4

logger = logging.getLogger(__name__)

_RESULT_MARKER = "__KW_STUDIO_RESULT_JSON__:"


@dataclass(frozen=True)
class KernelExecutionRequest:
    code: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class KernelExecutionResult:
    session_id: str
    status: str
    submitted_at: datetime
    completed_at: datetime | None = None
    stdout_text: str = ""
    stderr_text: str = ""
    output_text: str | None = None
    result_json: object | None = None
    exit_code: int | None = None
    timed_out: bool = False
    work_dir: str | None = None


@dataclass
class KernelSession:
    id: str
    work_dir: Path
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class KernelRuntime:
    """Controlled Python runtime boundary for the modular monolith.

    H1 intentionally keeps execution local and synchronous, but it now executes
    real Python code in a child process with explicit lifecycle, timeout,
    stdout/stderr capture, structured result capture, and cleanup behavior.
    """

    def __init__(self, *, temp_root: str | None = None, python_executable: str | None = None) -> None:
        self._sessions: dict[str, KernelSession] = {}
        self._lock = Lock()
        self._temp_root = Path(temp_root) if temp_root is not None else None
        self._python_executable = python_executable or sys.executable

    def create_session(self) -> KernelSession:
        work_dir = Path(tempfile.mkdtemp(prefix="kw-kernel-", dir=str(self._temp_root) if self._temp_root else None))
        session = KernelSession(id=f"kernel_{uuid4().hex}", work_dir=work_dir)
        with self._lock:
            self._sessions[session.id] = session
        logger.info("Kernel session created", extra={"session_id": session.id, "work_dir": str(work_dir)})
        return session

    def get_session(self, session_id: str) -> KernelSession | None:
        return self._sessions.get(session_id)

    def shutdown_session(self, session_id: str) -> bool:
        with self._lock:
            removed = self._sessions.pop(session_id, None)
        if removed is None:
            return False

        shutil.rmtree(removed.work_dir, ignore_errors=True)
        logger.info("Kernel session shutdown", extra={"session_id": session_id, "work_dir": str(removed.work_dir)})
        return True

    def execute(self, session_id: str, request: KernelExecutionRequest) -> KernelExecutionResult:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Unknown kernel session: {session_id}")

        submitted_at = datetime.now(timezone.utc)
        session.last_activity_at = submitted_at
        logger.info(
            "Kernel execution started",
            extra={"session_id": session_id, "timeout_seconds": request.timeout_seconds},
        )

        execution_dir = Path(tempfile.mkdtemp(prefix="exec-", dir=session.work_dir))
        script_path = execution_dir / "user_code.py"
        script_path.write_text(self._build_script(request.code), encoding="utf-8")

        try:
            completed = subprocess.run(
                [self._python_executable, str(script_path)],
                cwd=str(execution_dir),
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            completed_at = datetime.now(timezone.utc)
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
            shutil.rmtree(execution_dir, ignore_errors=True)
            return KernelExecutionResult(
                session_id=session_id,
                status="timed_out",
                submitted_at=submitted_at,
                completed_at=completed_at,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                output_text=stdout_text or None,
                exit_code=None,
                timed_out=True,
                work_dir=str(session.work_dir),
            )

        completed_at = datetime.now(timezone.utc)
        stdout_text, result_json = self._parse_stdout(completed.stdout)
        status = "succeeded" if completed.returncode == 0 else "failed"
        output_text = self._derive_output_text(stdout_text=stdout_text, result_json=result_json)
        shutil.rmtree(execution_dir, ignore_errors=True)

        return KernelExecutionResult(
            session_id=session_id,
            status=status,
            submitted_at=submitted_at,
            completed_at=completed_at,
            stdout_text=stdout_text,
            stderr_text=completed.stderr,
            output_text=output_text,
            result_json=result_json,
            exit_code=completed.returncode,
            timed_out=False,
            work_dir=str(session.work_dir),
        )

    @staticmethod
    def _build_script(code: str) -> str:
        executable_code = KernelRuntime._translate_legacy_marker_to_python(code)
        return (
            "import json\n"
            "namespace = {'__name__': '__main__'}\n"
            f"exec(compile({executable_code!r}, '<kw_user_code>', 'exec'), namespace, namespace)\n"
            "if 'result' in namespace:\n"
            f"    print({_RESULT_MARKER!r} + json.dumps(namespace['result'], ensure_ascii=False, default=str))\n"
        )

    @staticmethod
    def _translate_legacy_marker_to_python(code: str) -> str:
        """Compatibility shim for pre-H3 data-analysis callers.

        H1 makes the runtime real by executing this as Python in a child process.
        H3 can later move data analysis onto first-class engine-backed code
        without the legacy marker.
        """
        if not code.startswith("DATA_ANALYSIS::"):
            return code

        payload_raw = code.split("DATA_ANALYSIS::", 1)[1]
        payload = json.loads(payload_raw)
        content = payload.get("content", "")
        return f"""
import csv
import io

rows = list(csv.reader(io.StringIO({content!r})))
if not rows:
    result = "No rows detected in dataset."
else:
    header = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    numeric_values = []
    for row in data_rows:
        for value in row:
            try:
                numeric_values.append(float(value))
            except ValueError:
                pass
    numeric_mean_text = "n/a"
    if numeric_values:
        numeric_mean_text = f"{{sum(numeric_values) / len(numeric_values):.4f}}"
    result = (
        f"Rows: {{len(data_rows)}}\\n"
        f"Columns: {{len(header)}}\\n"
        f"Numeric cells: {{len(numeric_values)}}\\n"
        f"Numeric mean: {{numeric_mean_text}}"
    )
""".strip()

    @staticmethod
    def _parse_stdout(stdout_text: str) -> tuple[str, object | None]:
        cleaned_lines: list[str] = []
        result_json: object | None = None
        for line in stdout_text.splitlines():
            if line.startswith(_RESULT_MARKER):
                raw_result = line.removeprefix(_RESULT_MARKER)
                try:
                    result_json = json.loads(raw_result)
                except json.JSONDecodeError:
                    result_json = raw_result
                continue
            cleaned_lines.append(line)

        cleaned_stdout = "\n".join(cleaned_lines)
        if cleaned_stdout and stdout_text.endswith("\n"):
            cleaned_stdout += "\n"
        return cleaned_stdout, result_json

    @staticmethod
    def _derive_output_text(*, stdout_text: str, result_json: object | None) -> str | None:
        if isinstance(result_json, str):
            return result_json
        if result_json is not None:
            return json.dumps(result_json, ensure_ascii=False, default=str)
        return stdout_text or None

    def active_session_count(self) -> int:
        return len(self._sessions)
