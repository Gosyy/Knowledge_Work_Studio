from pathlib import Path

from backend.app.runtime.kernel import KernelExecutionRequest, KernelRuntime


def test_h1_kernel_runtime_executes_real_python_and_captures_stdout_stderr_and_result(tmp_path: Path) -> None:
    runtime = KernelRuntime(temp_root=str(tmp_path))
    session = runtime.create_session()

    result = runtime.execute(
        session.id,
        KernelExecutionRequest(
            code="""
import sys
print('hello stdout')
print('hello stderr', file=sys.stderr)
result = {'answer': 42}
""".strip(),
            timeout_seconds=5,
        ),
    )

    assert result.status == "succeeded"
    assert result.exit_code == 0
    assert result.stdout_text == "hello stdout\n"
    assert result.stderr_text == "hello stderr\n"
    assert result.result_json == {"answer": 42}
    assert result.output_text == '{"answer": 42}'
    assert result.timed_out is False
    assert result.work_dir is not None
    assert Path(result.work_dir).exists()

    assert runtime.shutdown_session(session.id) is True
    assert not Path(result.work_dir).exists()


def test_h1_kernel_runtime_reports_failures(tmp_path: Path) -> None:
    runtime = KernelRuntime(temp_root=str(tmp_path))
    session = runtime.create_session()

    result = runtime.execute(
        session.id,
        KernelExecutionRequest(code="raise RuntimeError('boom')", timeout_seconds=5),
    )

    assert result.status == "failed"
    assert result.exit_code != 0
    assert "RuntimeError: boom" in result.stderr_text
    assert result.timed_out is False
    assert runtime.shutdown_session(session.id) is True


def test_h1_kernel_runtime_enforces_timeout_and_cleans_execution_directory(tmp_path: Path) -> None:
    runtime = KernelRuntime(temp_root=str(tmp_path))
    session = runtime.create_session()

    result = runtime.execute(
        session.id,
        KernelExecutionRequest(
            code="""
import time
time.sleep(2)
""".strip(),
            timeout_seconds=1,
        ),
    )

    assert result.status == "timed_out"
    assert result.timed_out is True
    assert result.exit_code is None
    assert result.work_dir is not None
    assert Path(result.work_dir).exists()
    assert list(Path(result.work_dir).glob("exec-*")) == []

    assert runtime.shutdown_session(session.id) is True
    assert not Path(result.work_dir).exists()


def test_h1_kernel_runtime_keeps_legacy_data_analysis_compatibility_through_real_python(tmp_path: Path) -> None:
    runtime = KernelRuntime(temp_root=str(tmp_path))
    session = runtime.create_session()

    result = runtime.execute(
        session.id,
        KernelExecutionRequest(
            code='DATA_ANALYSIS::{"file_type":"csv","content":"a,b\\n1,2"}',
            timeout_seconds=5,
        ),
    )

    assert result.status == "succeeded"
    assert result.output_text == "Rows: 1\nColumns: 2\nNumeric cells: 2\nNumeric mean: 1.5000"
    assert result.result_json == "Rows: 1\nColumns: 2\nNumeric cells: 2\nNumeric mean: 1.5000"
    assert runtime.shutdown_session(session.id) is True
