from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

VISUAL_GRAMMAR_SCHEMA_VERSION = "presentation_visual_grammar.v1"

VisualGrammarBlockType = Literal[
    "executive_summary_cards",
    "kpi_cards",
    "process_flow",
    "roadmap",
    "timeline",
    "two_by_two_matrix",
    "swot",
    "comparison_table",
    "decision_matrix",
    "risk_matrix",
    "architecture_diagram",
    "funnel",
    "data_table",
    "native_chart",
]

_BLOCK_TYPES: tuple[str, ...] = (
    "executive_summary_cards",
    "kpi_cards",
    "process_flow",
    "roadmap",
    "timeline",
    "two_by_two_matrix",
    "swot",
    "comparison_table",
    "decision_matrix",
    "risk_matrix",
    "architecture_diagram",
    "funnel",
    "data_table",
    "native_chart",
)

_DIAGRAM_BLOCK_TYPES = {"process_flow", "roadmap", "timeline", "architecture_diagram", "funnel"}
_MATRIX_BLOCK_TYPES = {"two_by_two_matrix", "swot", "decision_matrix", "risk_matrix"}
_TABLE_BLOCK_TYPES = {"comparison_table", "data_table"}


@dataclass(frozen=True)
class VisualGrammarBlockSpec:
    block_type: str
    semantic_purpose: str
    required_content_keys: tuple[str, ...]
    required_data_binding_keys: tuple[str, ...] = ()
    requires_source_ref: bool = True
    requires_numeric_data: bool = False
    requires_nodes_or_items: bool = False
    renderer_readiness: Literal["contract_only", "renderer_ready"] = "contract_only"
    prohibited_claims: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_content_keys"] = list(self.required_content_keys)
        payload["required_data_binding_keys"] = list(self.required_data_binding_keys)
        payload["prohibited_claims"] = list(self.prohibited_claims)
        return payload


@dataclass(frozen=True)
class VisualGrammarValidationIssue:
    code: str
    message: str
    block_id: str | None = None
    block_type: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualGrammarValidationResult:
    schema_version: str
    status: Literal["ready", "blocked"]
    block_type: str
    block_id: str | None
    issues: tuple[VisualGrammarValidationIssue, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "block_type": self.block_type,
            "block_id": self.block_id,
            "issues": [issue.as_dict() for issue in self.issues],
        }


class PresentationVisualGrammarLibrary:
    """KR-7G.1 professional editable block grammar foundation.

    This library defines semantic block contracts and validators only. It does not render PPTX, call LLMs, create charts, generate images, or fabricate data. Native chart blocks must point to real source data refs and include
    numeric series before later renderer phases may use them.
    """

    def __init__(self) -> None:
        self._specs = _build_default_specs()

    @property
    def schema_version(self) -> str:
        return VISUAL_GRAMMAR_SCHEMA_VERSION

    def list_specs(self) -> tuple[VisualGrammarBlockSpec, ...]:
        return tuple(self._specs[block_type] for block_type in _BLOCK_TYPES)

    def get_spec(self, block_type: str) -> VisualGrammarBlockSpec:
        if block_type not in self._specs:
            raise ValueError(f"Unsupported visual grammar block_type: {block_type}")
        return self._specs[block_type]

    def validate_block(self, block: dict[str, Any]) -> VisualGrammarValidationResult:
        block_id = _string_or_none(block.get("block_id"))
        block_type = str(block.get("type") or "").strip()
        if block_type not in self._specs:
            issue = VisualGrammarValidationIssue(
                code="unsupported_visual_grammar_block_type",
                message="Block type is not part of presentation_visual_grammar.v1.",
                block_id=block_id,
                block_type=block_type or None,
            )
            return VisualGrammarValidationResult(
                schema_version=VISUAL_GRAMMAR_SCHEMA_VERSION,
                status="blocked",
                block_type=block_type or "unknown",
                block_id=block_id,
                issues=(issue,),
            )
        spec = self._specs[block_type]
        issues: list[VisualGrammarValidationIssue] = []
        content = block.get("content")
        if not isinstance(content, dict):
            issues.append(_issue("content_must_be_object", "Block content must be an object.", block_id, block_type))
            content = {}
        for key in spec.required_content_keys:
            if key not in content:
                issues.append(_issue("missing_required_content_key", f"Missing content.{key}.", block_id, block_type))

        semantic_role = str(block.get("semantic_role") or "").strip()
        if not semantic_role:
            issues.append(_issue("missing_semantic_role", "Every visual grammar block must declare semantic_role.", block_id, block_type))

        source_refs = block.get("source_refs")
        if spec.requires_source_ref and not _non_empty_string_list(source_refs):
            issues.append(_issue("missing_source_refs", "Block must reference local source evidence or source asset ids.", block_id, block_type))

        data_binding = block.get("data_binding")
        if spec.required_data_binding_keys:
            if not isinstance(data_binding, dict):
                issues.append(_issue("missing_data_binding", "Block data_binding must be an object.", block_id, block_type))
                data_binding = {}
            for key in spec.required_data_binding_keys:
                if key not in data_binding:
                    issues.append(_issue("missing_data_binding_key", f"Missing data_binding.{key}.", block_id, block_type))

        if spec.requires_nodes_or_items and not _has_nodes_edges_or_items(content):
            issues.append(_issue("missing_diagram_nodes_or_items", "Diagram block must include nodes, edges, steps, phases, or items.", block_id, block_type))

        if spec.requires_numeric_data and not _has_numeric_series(content, data_binding if isinstance(data_binding, dict) else {}):
            issues.append(_issue("native_chart_requires_real_numeric_data", "Native chart block requires real numeric series and a source data ref.", block_id, block_type))

        status: Literal["ready", "blocked"] = "ready" if not issues else "blocked"
        return VisualGrammarValidationResult(
            schema_version=VISUAL_GRAMMAR_SCHEMA_VERSION,
            status=status,
            block_type=block_type,
            block_id=block_id,
            issues=tuple(issues),
        )

    def validate_presentation_ir_blocks(self, presentation_ir: dict[str, Any]) -> tuple[VisualGrammarValidationResult, ...]:
        results: list[VisualGrammarValidationResult] = []
        for slide in presentation_ir.get("slides") or []:
            if not isinstance(slide, dict):
                continue
            for block in slide.get("blocks") or []:
                if isinstance(block, dict) and block.get("type") in self._specs:
                    results.append(self.validate_block(block))
        return tuple(results)


def visual_grammar_catalog_payload() -> dict[str, Any]:
    library = PresentationVisualGrammarLibrary()
    return {
        "schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
        "block_count": len(library.list_specs()),
        "blocks": [spec.as_dict() for spec in library.list_specs()],
        "non_goals": [
            "no_pptx_rendering",
            "no_llm_runtime",
            "no_generated_images",
            "no_fake_charts_or_values",
        ],
    }


def _build_default_specs() -> dict[str, VisualGrammarBlockSpec]:
    common_source_claims = ("do_not_claim_renderer_runtime", "do_not_fabricate_source_data")
    return {
        "executive_summary_cards": VisualGrammarBlockSpec(
            block_type="executive_summary_cards",
            semantic_purpose="Summarize the most important source-backed takeaways as editable cards.",
            required_content_keys=("cards",),
            prohibited_claims=common_source_claims,
        ),
        "kpi_cards": VisualGrammarBlockSpec(
            block_type="kpi_cards",
            semantic_purpose="Show evidence-backed KPI values as editable cards.",
            required_content_keys=("kpis",),
            required_data_binding_keys=("source_ref",),
            prohibited_claims=common_source_claims,
        ),
        "process_flow": VisualGrammarBlockSpec(
            block_type="process_flow",
            semantic_purpose="Represent ordered process steps as editable nodes and connectors.",
            required_content_keys=("steps",),
            requires_nodes_or_items=True,
            prohibited_claims=common_source_claims,
        ),
        "roadmap": VisualGrammarBlockSpec(
            block_type="roadmap",
            semantic_purpose="Represent phased plan milestones as editable timeline groups.",
            required_content_keys=("phases",),
            requires_nodes_or_items=True,
            prohibited_claims=common_source_claims,
        ),
        "timeline": VisualGrammarBlockSpec(
            block_type="timeline",
            semantic_purpose="Represent dated or sequenced events as editable timeline markers.",
            required_content_keys=("items",),
            requires_nodes_or_items=True,
            prohibited_claims=common_source_claims,
        ),
        "two_by_two_matrix": VisualGrammarBlockSpec(
            block_type="two_by_two_matrix",
            semantic_purpose="Represent four-quadrant analysis as editable matrix cells.",
            required_content_keys=("quadrants",),
            prohibited_claims=common_source_claims,
        ),
        "swot": VisualGrammarBlockSpec(
            block_type="swot",
            semantic_purpose="Represent strengths, weaknesses, opportunities, and threats as editable matrix groups.",
            required_content_keys=("strengths", "weaknesses", "opportunities", "threats"),
            prohibited_claims=common_source_claims,
        ),
        "comparison_table": VisualGrammarBlockSpec(
            block_type="comparison_table",
            semantic_purpose="Compare source-backed options in an editable table.",
            required_content_keys=("columns", "rows"),
            prohibited_claims=common_source_claims,
        ),
        "decision_matrix": VisualGrammarBlockSpec(
            block_type="decision_matrix",
            semantic_purpose="Compare options against decision criteria as editable cells.",
            required_content_keys=("criteria", "options", "scores"),
            prohibited_claims=common_source_claims,
        ),
        "risk_matrix": VisualGrammarBlockSpec(
            block_type="risk_matrix",
            semantic_purpose="Show risks by likelihood and impact as editable matrix entries.",
            required_content_keys=("risks",),
            prohibited_claims=common_source_claims,
        ),
        "architecture_diagram": VisualGrammarBlockSpec(
            block_type="architecture_diagram",
            semantic_purpose="Represent architecture components and relationships as editable nodes and edges.",
            required_content_keys=("nodes", "edges"),
            requires_nodes_or_items=True,
            prohibited_claims=common_source_claims,
        ),
        "funnel": VisualGrammarBlockSpec(
            block_type="funnel",
            semantic_purpose="Represent funnel stages as editable ordered bands.",
            required_content_keys=("stages",),
            requires_nodes_or_items=True,
            prohibited_claims=common_source_claims,
        ),
        "data_table": VisualGrammarBlockSpec(
            block_type="data_table",
            semantic_purpose="Show source-backed tabular data as editable table cells.",
            required_content_keys=("columns", "rows"),
            required_data_binding_keys=("source_ref",),
            prohibited_claims=common_source_claims,
        ),
        "native_chart": VisualGrammarBlockSpec(
            block_type="native_chart",
            semantic_purpose="Describe a future native editable chart backed by real numeric source data.",
            required_content_keys=("chart_type", "series"),
            required_data_binding_keys=("source_ref", "data_ref"),
            requires_numeric_data=True,
            prohibited_claims=("do_not_create_fake_chart_values", "do_not_claim_renderer_runtime"),
        ),
    }


def _issue(code: str, message: str, block_id: str | None, block_type: str | None) -> VisualGrammarValidationIssue:
    return VisualGrammarValidationIssue(code=code, message=message, block_id=block_id, block_type=block_type)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _has_nodes_edges_or_items(content: dict[str, Any]) -> bool:
    for key in ("nodes", "edges", "steps", "phases", "items", "stages"):
        value = content.get(key)
        if isinstance(value, list) and value:
            return True
    return False


def _has_numeric_series(content: dict[str, Any], data_binding: dict[str, Any]) -> bool:
    if not data_binding.get("source_ref") or not data_binding.get("data_ref"):
        return False
    series = content.get("series")
    if not isinstance(series, list) or not series:
        return False
    for item in series:
        if isinstance(item, dict):
            values = item.get("values")
        else:
            values = item
        if not isinstance(values, list) or not values:
            return False
        for value in values:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
    return True


__all__ = [
    "VISUAL_GRAMMAR_SCHEMA_VERSION",
    "PresentationVisualGrammarLibrary",
    "VisualGrammarBlockSpec",
    "VisualGrammarValidationIssue",
    "VisualGrammarValidationResult",
    "visual_grammar_catalog_payload",
]
