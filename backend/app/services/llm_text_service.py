from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.domain import LLMRun
from backend.app.integrations.llm import LLMCompletionRequest, LLMCompletionResult, LLMProvider
from backend.app.repositories import LLMRunRepository


@dataclass
class LLMTextService:
    provider: LLMProvider
    llm_runs: LLMRunRepository | None = None

    def complete_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        workflow: str = "completion",
        task_id: str | None = None,
    ) -> str:
        result = self._complete(
            prompt=prompt,
            system_prompt=system_prompt,
            workflow=workflow,
            task_id=task_id,
        )
        return result.text

    def classify_task(self, prompt: str, *, task_id: str | None = None) -> str:
        return self.complete_prompt(
            prompt=prompt,
            system_prompt=(
                "Classify the user's request into exactly one task type: "
                "docx_edit, pdf_summary, slides_generate, data_analysis. "
                "Return only the task type."
            ),
            workflow="classification",
            task_id=task_id,
        ).strip()

    def summarize_text(self, text: str, *, task_id: str | None = None) -> str:
        return self.complete_prompt(
            prompt=text,
            system_prompt="Summarize the provided text clearly and concisely.",
            workflow="summarization",
            task_id=task_id,
        )

    def rewrite_text(self, text: str, *, instruction: str, task_id: str | None = None) -> str:
        return self.complete_prompt(
            prompt=f"Instruction: {instruction}\n\nText:\n{text}",
            system_prompt="Rewrite the provided text according to the instruction.",
            workflow="rewriting",
            task_id=task_id,
        )

    def generate_outline(self, prompt: str, *, task_id: str | None = None) -> str:
        return self.complete_prompt(
            prompt=prompt,
            system_prompt="Generate a concise structured outline.",
            workflow="outline_generation",
            task_id=task_id,
        )

    def _complete(
        self,
        *,
        prompt: str,
        system_prompt: str | None,
        workflow: str,
        task_id: str | None,
    ) -> LLMCompletionResult:
        started_at = datetime.now(timezone.utc)
        request = LLMCompletionRequest(prompt=prompt, system_prompt=system_prompt)
        try:
            result = self.provider.complete(request)
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            self._record_run(
                task_id=task_id,
                workflow=workflow,
                provider=getattr(self.provider, "provider_name", "unknown"),
                model="unknown",
                prompt=prompt,
                system_prompt=system_prompt,
                response_text="",
                status="failed",
                error_message=str(exc),
                raw_json=None,
                started_at=started_at,
                completed_at=completed_at,
            )
            raise

        completed_at = datetime.now(timezone.utc)
        self._record_run(
            task_id=task_id,
            workflow=workflow,
            provider=result.provider,
            model=result.model,
            prompt=prompt,
            system_prompt=system_prompt,
            response_text=result.text,
            status="succeeded",
            error_message=None,
            raw_json=result.raw,
            started_at=started_at,
            completed_at=completed_at,
        )
        return result

    def _record_run(
        self,
        *,
        task_id: str | None,
        workflow: str,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: str | None,
        response_text: str,
        status: str,
        error_message: str | None,
        raw_json: dict[str, object] | None,
        started_at: datetime,
        completed_at: datetime,
    ) -> None:
        if self.llm_runs is None:
            return
        self.llm_runs.create(
            LLMRun(
                id=f"llmrun_{uuid4().hex}",
                task_id=task_id,
                workflow=workflow,
                provider=provider,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                response_text=response_text,
                status=status,
                error_message=error_message,
                raw_json=raw_json,
                started_at=started_at,
                completed_at=completed_at,
            )
        )
