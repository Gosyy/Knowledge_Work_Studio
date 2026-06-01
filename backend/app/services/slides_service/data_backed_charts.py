from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

from backend.app.services.slides_service.offline_source_ingestion import (
    SourceChartDataCandidate,
    SourceTableCandidate,
)

DATA_BACKED_CHARTS_SCHEMA_VERSION = "presentation_data_backed_charts.v1"
DATA_BACKED_CHARTS_PHASE = "KR-7K data-backed charts"

DataBackedChartStatus = Literal["ready", "degraded", "blocked"]
DataChartBindingStatus = Literal["bound", "blocked"]

_SUPPORTED_CHART_TYPES = {"bar", "column", "line", "area", "pie", "scatter"}
_ALLOWED_SOURCE_KINDS = {"extracted_table", "extracted_chart_candidate", "user_provided_numeric_data"}
_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{2,}", flags=re.UNICODE)
_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*•‣◦]|\d+[.)])\s+")


@dataclass(frozen=True)
class DataChartSeries:
    name: str
    values: tuple[float, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["values"] = list(self.values)
        return payload


@dataclass(frozen=True)
class DataChartSourceCandidate:
    data_id: str
    source_kind: str
    source_id: str
    provenance_ref: str
    data_ref: str
    labels: tuple[str, ...]
    series: tuple[DataChartSeries, ...]
    chart_type_hint: str = "bar"
    units: str | None = None
    sheet_name: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    source_table_id: str | None = None
    source_chart_candidate_id: str | None = None
    source_backed: bool = True
    generated_data: bool = False
    fake_data: bool = False
    random_data: bool = False
    bullet_length_chart: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["labels"] = list(self.labels)
        payload["series"] = [serie.as_dict() for serie in self.series]
        return payload


@dataclass(frozen=True)
class DataChartRequest:
    slide_id: str
    block_id: str
    role: str
    title: str
    intent_query: str = ""
    chart_type: str = "bar"
    expected_terms: tuple[str, ...] = ()
    requires_chart: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_terms"] = list(self.expected_terms)
        return payload


@dataclass(frozen=True)
class DataChartBinding:
    slide_id: str
    block_id: str
    status: DataChartBindingStatus
    chart_type: str
    data_id: str | None
    data_ref: str | None
    provenance_ref: str | None
    source_id: str | None
    labels: tuple[str, ...]
    series: tuple[DataChartSeries, ...]
    units: str | None
    relevance_score: float
    binding_score: float
    matched_terms: tuple[str, ...] = ()
    blocked_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["labels"] = list(self.labels)
        payload["series"] = [serie.as_dict() for serie in self.series]
        payload["matched_terms"] = list(self.matched_terms)
        return payload


@dataclass(frozen=True)
class DataBackedChartResult:
    schema_version: str
    phase: str
    status: DataBackedChartStatus
    data_backed_charts_implemented: bool
    chart_intent_classification_implemented: bool
    numeric_series_validation_implemented: bool
    chart_data_binding_implemented: bool
    source_refs_required: bool
    no_fake_charts_enforced: bool
    bound_chart_count: int
    candidate_count: int
    chart_request_count: int
    candidates: tuple[DataChartSourceCandidate, ...] = ()
    chart_bindings: tuple[DataChartBinding, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    generated_chart_data_allowed: bool = False
    random_chart_data_allowed: bool = False
    fake_chart_data_allowed: bool = False
    bullet_length_charts_allowed: bool = False
    chart_without_data_source_allowed: bool = False
    renderer_runtime_changed: bool = False
    native_chart_rendering_implemented: bool = False
    renderer_chart_mapping_implemented: bool = False
    visual_qa_executed: bool = False
    kimi_level_quality_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "status": self.status,
            "data_backed_charts_implemented": self.data_backed_charts_implemented,
            "chart_intent_classification_implemented": self.chart_intent_classification_implemented,
            "numeric_series_validation_implemented": self.numeric_series_validation_implemented,
            "chart_data_binding_implemented": self.chart_data_binding_implemented,
            "source_refs_required": self.source_refs_required,
            "no_fake_charts_enforced": self.no_fake_charts_enforced,
            "bound_chart_count": self.bound_chart_count,
            "candidate_count": self.candidate_count,
            "chart_request_count": self.chart_request_count,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "chart_bindings": [binding.as_dict() for binding in self.chart_bindings],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "generated_chart_data_allowed": self.generated_chart_data_allowed,
            "random_chart_data_allowed": self.random_chart_data_allowed,
            "fake_chart_data_allowed": self.fake_chart_data_allowed,
            "bullet_length_charts_allowed": self.bullet_length_charts_allowed,
            "chart_without_data_source_allowed": self.chart_without_data_source_allowed,
            "renderer_runtime_changed": self.renderer_runtime_changed,
            "native_chart_rendering_implemented": self.native_chart_rendering_implemented,
            "renderer_chart_mapping_implemented": self.renderer_chart_mapping_implemented,
            "visual_qa_executed": self.visual_qa_executed,
            "kimi_level_quality_claimed": self.kimi_level_quality_claimed,
            "non_goals": [
                "no_renderer_chart_mapping_runtime",
                "no_native_chart_rendering_runtime",
                "no_fake_chart_values",
                "no_generated_chart_data",
                "no_random_chart_values",
                "no_bullet_length_charts",
                "no_visual_qa_scoring",
                "no_kimi_level_quality_claim",
                "no_ui_changes",
                "no_gigachat_runtime_changes",
                "no_docker_deploy_postgres_changes",
            ],
        }


def bind_data_backed_charts(
    chart_requests: Iterable[DataChartRequest | dict[str, Any]],
    *,
    source_tables: Iterable[SourceTableCandidate | dict[str, Any]] = (),
    source_chart_candidates: Iterable[SourceChartDataCandidate | dict[str, Any]] = (),
    user_data_candidates: Iterable[DataChartSourceCandidate | dict[str, Any]] = (),
    min_relevance_score: float = 0.10,
) -> DataBackedChartResult:
    """Bind chart intents only to real numeric source data.

    KR-7K emits deterministic chart data bindings/specs. It does not render
    native charts into PPTX, invoke an LLM, fabricate values, or treat bullet
    text as chart data.
    """

    warnings: list[str] = []
    errors: list[str] = []
    requests = tuple(_coerce_chart_request(request) for request in chart_requests)
    candidates = [
        *_candidates_from_tables(source_tables),
        *_candidates_from_chart_candidates(source_chart_candidates),
        *(_coerce_candidate(candidate) for candidate in user_data_candidates),
    ]
    candidates = _deduplicate_candidates(candidates)
    valid_candidates = [candidate for candidate in candidates if _candidate_is_valid(candidate, errors)]
    if len(valid_candidates) < len(candidates):
        warnings.append("some chart data candidates were rejected because they were not real numeric source data")

    bindings = tuple(
        _bind_chart_request(request, valid_candidates, min_relevance_score=min_relevance_score)
        for request in requests
    )
    for binding in bindings:
        if binding.status == "blocked":
            errors.append(f"chart {binding.block_id} blocked: {binding.blocked_reason}")

    bound_count = sum(1 for binding in bindings if binding.status == "bound")
    if errors:
        status: DataBackedChartStatus = "blocked"
    elif requests and bound_count < len(requests):
        status = "degraded"
    else:
        status = "ready"

    return DataBackedChartResult(
        schema_version=DATA_BACKED_CHARTS_SCHEMA_VERSION,
        phase=DATA_BACKED_CHARTS_PHASE,
        status=status,
        data_backed_charts_implemented=True,
        chart_intent_classification_implemented=True,
        numeric_series_validation_implemented=True,
        chart_data_binding_implemented=True,
        source_refs_required=True,
        no_fake_charts_enforced=True,
        bound_chart_count=bound_count,
        candidate_count=len(valid_candidates),
        chart_request_count=len(requests),
        candidates=tuple(valid_candidates),
        chart_bindings=bindings,
        warnings=tuple(_unique(warnings)),
        errors=tuple(_unique(errors)),
    )


def sample_data_backed_chart_report() -> dict[str, Any]:
    revenue_table = SourceTableCandidate(
        table_id="revenue_table",
        source_id="uploaded_finance_workbook",
        rows=[
            ["Quarter", "Revenue", "Cost"],
            ["Q1", "120", "75"],
            ["Q2", "135", "80"],
            ["Q3", "160", "92"],
            ["Q4", "172", "101"],
        ],
        provenance_ref="uploaded_finance_workbook#xlsx-sheet:1!A1:C5",
        caption="Quarterly revenue and cost, USD thousands",
        sheet_name="Finance",
    )
    request = DataChartRequest(
        slide_id="s003",
        block_id="s003_revenue_chart",
        role="data",
        title="Quarterly revenue chart",
        intent_query="quarterly revenue cost chart",
        chart_type="line",
        expected_terms=("quarter", "revenue", "cost"),
        requires_chart=True,
    )
    return bind_data_backed_charts([request], source_tables=[revenue_table]).as_dict()


def _coerce_chart_request(value: DataChartRequest | dict[str, Any]) -> DataChartRequest:
    if isinstance(value, DataChartRequest):
        return value
    expected_terms = value.get("expected_terms") or value.get("terms") or ()
    if isinstance(expected_terms, str):
        expected_terms = (expected_terms,)
    return DataChartRequest(
        slide_id=str(value.get("slide_id") or value.get("id") or "unknown_slide"),
        block_id=str(value.get("block_id") or value.get("chart_id") or "unknown_chart"),
        role=str(value.get("role") or value.get("semantic_role") or "data"),
        title=str(value.get("title") or ""),
        intent_query=str(value.get("intent_query") or value.get("query") or ""),
        chart_type=_normalize_chart_type(str(value.get("chart_type") or "bar")),
        expected_terms=tuple(str(term) for term in expected_terms),
        requires_chart=bool(value.get("requires_chart", False)),
    )


def _candidates_from_tables(source_tables: Iterable[SourceTableCandidate | dict[str, Any]]) -> list[DataChartSourceCandidate]:
    candidates: list[DataChartSourceCandidate] = []
    for index, table in enumerate(source_tables, start=1):
        payload = table.as_dict() if hasattr(table, "as_dict") else dict(table)
        rows = payload.get("rows") or []
        candidate = _candidate_from_table_payload(payload, rows, index=index)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _candidate_from_table_payload(payload: dict[str, Any], rows: list[list[Any]], *, index: int) -> DataChartSourceCandidate | None:
    if len(rows) < 2:
        return None
    normalized_rows = [[str(cell).strip() for cell in row] for row in rows if any(str(cell).strip() for cell in row)]
    if len(normalized_rows) < 2:
        return None
    header = normalized_rows[0]
    body = normalized_rows[1:]
    if not header or len(header) < 2:
        return None
    labels: list[str] = []
    numeric_columns: dict[int, list[float]] = {column_index: [] for column_index in range(1, len(header))}
    bullet_like = False
    for row in body:
        if not row:
            continue
        label = row[0].strip()
        bullet_like = bullet_like or _looks_like_bullet(label) or any(_looks_like_bullet(cell) for cell in row[1:])
        if not label:
            continue
        labels.append(label)
        for column_index in range(1, len(header)):
            value = row[column_index] if column_index < len(row) else ""
            numeric = _parse_number(value)
            if numeric is None:
                numeric_columns[column_index].append(math.nan)
            else:
                numeric_columns[column_index].append(numeric)
    if not labels:
        return None
    series: list[DataChartSeries] = []
    for column_index, values in numeric_columns.items():
        if not values or any(math.isnan(value) for value in values):
            continue
        if len(values) != len(labels):
            continue
        series.append(DataChartSeries(name=str(header[column_index] or f"series_{column_index}"), values=tuple(values)))
    if not series:
        return None
    source_id = str(payload.get("source_id") or "unknown_source")
    table_id = str(payload.get("table_id") or f"table_{index:03d}")
    provenance_ref = str(payload.get("provenance_ref") or "")
    units = _infer_units(payload.get("caption"), header)
    return DataChartSourceCandidate(
        data_id=f"table_chart_data_{_safe_id(table_id)}",
        source_kind="extracted_table",
        source_id=source_id,
        provenance_ref=provenance_ref,
        data_ref=f"{provenance_ref or source_id}#{table_id}",
        labels=tuple(labels),
        series=tuple(series),
        chart_type_hint="line" if len(labels) >= 3 else "bar",
        units=units,
        sheet_name=payload.get("sheet_name"),
        page_number=_int_or_none(payload.get("page_number")),
        slide_number=_int_or_none(payload.get("slide_number")),
        source_table_id=table_id,
        bullet_length_chart=bullet_like,
    )


def _candidates_from_chart_candidates(
    source_chart_candidates: Iterable[SourceChartDataCandidate | dict[str, Any]],
) -> list[DataChartSourceCandidate]:
    candidates: list[DataChartSourceCandidate] = []
    for index, chart in enumerate(source_chart_candidates, start=1):
        payload = chart.as_dict() if hasattr(chart, "as_dict") else dict(chart)
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        labels = tuple(str(item) for item in metadata.get("labels") or ())
        series_payload = metadata.get("series") or metadata.get("numeric_series") or ()
        series = _series_from_payload(series_payload)
        if not labels or not series:
            continue
        source_id = str(payload.get("source_id") or "unknown_source")
        candidate_id = str(payload.get("candidate_id") or f"chart_candidate_{index:03d}")
        provenance_ref = str(payload.get("provenance_ref") or "")
        data_refs = payload.get("data_refs") or []
        data_ref = str(data_refs[0]) if data_refs else f"{provenance_ref}#{candidate_id}"
        candidates.append(
            DataChartSourceCandidate(
                data_id=f"source_chart_data_{_safe_id(candidate_id)}",
                source_kind="extracted_chart_candidate",
                source_id=source_id,
                provenance_ref=provenance_ref,
                data_ref=data_ref,
                labels=labels,
                series=series,
                chart_type_hint=_normalize_chart_type(str(payload.get("chart_type") or "bar")),
                units=metadata.get("units"),
                sheet_name=payload.get("sheet_name"),
                slide_number=_int_or_none(payload.get("slide_number")),
                source_chart_candidate_id=candidate_id,
                generated_data=_marker(payload, "generated"),
                fake_data=_marker(payload, "fake"),
                random_data=_marker(payload, "random"),
                bullet_length_chart=_series_looks_bullet_like(labels, series),
            )
        )
    return candidates


def _coerce_candidate(value: DataChartSourceCandidate | dict[str, Any]) -> DataChartSourceCandidate:
    if isinstance(value, DataChartSourceCandidate):
        return value
    payload = dict(value)
    return DataChartSourceCandidate(
        data_id=str(payload.get("data_id") or payload.get("id") or "user_chart_data"),
        source_kind=str(payload.get("source_kind") or "user_provided_numeric_data"),
        source_id=str(payload.get("source_id") or "user_provided"),
        provenance_ref=str(payload.get("provenance_ref") or ""),
        data_ref=str(payload.get("data_ref") or ""),
        labels=tuple(str(label) for label in payload.get("labels") or ()),
        series=_series_from_payload(payload.get("series") or ()),
        chart_type_hint=_normalize_chart_type(str(payload.get("chart_type_hint") or payload.get("chart_type") or "bar")),
        units=payload.get("units"),
        sheet_name=payload.get("sheet_name"),
        page_number=_int_or_none(payload.get("page_number")),
        slide_number=_int_or_none(payload.get("slide_number")),
        source_table_id=payload.get("source_table_id"),
        source_chart_candidate_id=payload.get("source_chart_candidate_id"),
        source_backed=bool(payload.get("source_backed", True)),
        generated_data=bool(payload.get("generated_data", False)),
        fake_data=bool(payload.get("fake_data", False)),
        random_data=bool(payload.get("random_data", False)),
        bullet_length_chart=bool(payload.get("bullet_length_chart", False)) or _series_looks_bullet_like(payload.get("labels") or (), _series_from_payload(payload.get("series") or ())),
    )


def _candidate_is_valid(candidate: DataChartSourceCandidate, errors: list[str]) -> bool:
    if candidate.source_kind not in _ALLOWED_SOURCE_KINDS:
        errors.append(f"chart data candidate {candidate.data_id} has unsupported source kind")
        return False
    if not candidate.source_backed or candidate.generated_data or candidate.fake_data or candidate.random_data:
        errors.append(f"chart data candidate {candidate.data_id} is not source-backed real data")
        return False
    if candidate.bullet_length_chart:
        errors.append(f"chart data candidate {candidate.data_id} looks like bullet text instead of numeric chart data")
        return False
    if not candidate.provenance_ref or not candidate.data_ref:
        errors.append(f"chart data candidate {candidate.data_id} lacks provenance_ref or data_ref")
        return False
    if len(candidate.labels) < 2:
        errors.append(f"chart data candidate {candidate.data_id} needs at least two labels")
        return False
    if not candidate.series:
        errors.append(f"chart data candidate {candidate.data_id} lacks numeric series")
        return False
    for series in candidate.series:
        if len(series.values) != len(candidate.labels):
            errors.append(f"chart data candidate {candidate.data_id} series length does not match labels")
            return False
        if not series.values or any(not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in series.values):
            errors.append(f"chart data candidate {candidate.data_id} contains non-numeric or non-finite values")
            return False
    return True


def _bind_chart_request(
    request: DataChartRequest,
    candidates: list[DataChartSourceCandidate],
    *,
    min_relevance_score: float,
) -> DataChartBinding:
    if _normalize_chart_type(request.chart_type) not in _SUPPORTED_CHART_TYPES:
        return _blocked_binding(request, "unsupported_chart_type")
    scored: list[tuple[float, float, tuple[str, ...], DataChartSourceCandidate]] = []
    for candidate in candidates:
        relevance, matched = _relevance_score(request, candidate)
        chart_type_bonus = 0.08 if _normalize_chart_type(request.chart_type) == _normalize_chart_type(candidate.chart_type_hint) else 0.0
        density_bonus = min(len(candidate.series) * len(candidate.labels) / 100.0, 0.10)
        binding_score = round((relevance * 0.75) + chart_type_bonus + density_bonus, 4)
        scored.append((binding_score, relevance, matched, candidate))
    scored.sort(key=lambda item: (-item[0], item[3].data_id))
    if scored and scored[0][1] >= min_relevance_score:
        binding_score, relevance, matched, candidate = scored[0]
        return DataChartBinding(
            slide_id=request.slide_id,
            block_id=request.block_id,
            status="bound",
            chart_type=_normalize_chart_type(request.chart_type),
            data_id=candidate.data_id,
            data_ref=candidate.data_ref,
            provenance_ref=candidate.provenance_ref,
            source_id=candidate.source_id,
            labels=candidate.labels,
            series=candidate.series,
            units=candidate.units or "unknown",
            relevance_score=relevance,
            binding_score=binding_score,
            matched_terms=matched,
        )
    reason = "required_chart_has_no_real_numeric_source_data" if request.requires_chart else "no_relevant_numeric_source_data"
    return _blocked_binding(request, reason)


def _blocked_binding(request: DataChartRequest, reason: str) -> DataChartBinding:
    return DataChartBinding(
        slide_id=request.slide_id,
        block_id=request.block_id,
        status="blocked",
        chart_type=_normalize_chart_type(request.chart_type),
        data_id=None,
        data_ref=None,
        provenance_ref=None,
        source_id=None,
        labels=(),
        series=(),
        units=None,
        relevance_score=0.0,
        binding_score=0.0,
        matched_terms=(),
        blocked_reason=reason,
    )


def _relevance_score(request: DataChartRequest, candidate: DataChartSourceCandidate) -> tuple[float, tuple[str, ...]]:
    requested_tokens = _tokens(" ".join([request.title, request.intent_query, request.role, *request.expected_terms]))
    if not requested_tokens:
        return (0.0, ())
    candidate_tokens = _tokens(
        " ".join(
            [
                candidate.data_id,
                candidate.source_id,
                candidate.provenance_ref,
                candidate.data_ref,
                candidate.units or "",
                candidate.sheet_name or "",
                *(candidate.labels),
                *(series.name for series in candidate.series),
            ]
        )
    )
    matched = tuple(sorted(requested_tokens & candidate_tokens))
    if not matched:
        return (0.0, ())
    return (round(len(matched) / max(len(requested_tokens), 1), 4), matched)


def _series_from_payload(values: Any) -> tuple[DataChartSeries, ...]:
    series: list[DataChartSeries] = []
    for index, item in enumerate(values or (), start=1):
        if isinstance(item, DataChartSeries):
            series.append(item)
            continue
        if not isinstance(item, dict):
            continue
        parsed_values: list[float] = []
        for value in item.get("values") or ():
            number = _parse_number(value)
            if number is None:
                parsed_values = []
                break
            parsed_values.append(number)
        if parsed_values:
            series.append(DataChartSeries(name=str(item.get("name") or f"series_{index}"), values=tuple(parsed_values)))
    return tuple(series)


def _parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    cleaned = text.replace("\u00a0", " ").replace("%", "").strip()
    cleaned = re.sub(r"[^0-9,().+\-\s]", "", cleaned)
    cleaned = cleaned.replace(" ", "")
    if cleaned.count(",") == 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def _normalize_chart_type(value: str) -> str:
    normalized = str(value or "bar").strip().lower().replace("chart", "").strip("_ -")
    aliases = {"bar": "bar", "column": "column", "bar3d": "bar", "line": "line", "line3d": "line", "pie": "pie", "area": "area", "scatter": "scatter", "scatterchart": "scatter"}
    return aliases.get(normalized, normalized or "bar")


def _infer_units(caption: Any, header: list[str]) -> str | None:
    text = " ".join(str(item or "") for item in [caption, *header]).lower()
    if "usd" in text or "$" in text:
        return "USD"
    if "%" in text or "percent" in text or "процент" in text:
        return "percent"
    if "руб" in text or "rub" in text:
        return "RUB"
    return "unknown"


def _series_looks_bullet_like(labels: Iterable[Any], series: Iterable[DataChartSeries]) -> bool:
    if any(_looks_like_bullet(str(label)) or len(str(label)) > 80 for label in labels):
        return True
    return any(_looks_like_bullet(series_item.name) or len(series_item.name) > 80 for series_item in series)


def _looks_like_bullet(value: str) -> bool:
    return bool(_BULLET_PREFIX_RE.match(str(value or "")))


def _marker(payload: dict[str, Any], marker: str) -> bool:
    if bool(payload.get(f"{marker}_data")) or bool(payload.get(f"{marker}_chart")):
        return True
    encoded = " ".join(str(payload.get(key, "")) for key in ("candidate_id", "data_id", "title", "provenance_ref", "data_refs"))
    return marker in encoded.lower()


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"[_./#:-]+", " ", text or "")
    return {token.lower() for token in _TOKEN_RE.findall(normalized) if len(token) >= 2}


def _deduplicate_candidates(candidates: list[DataChartSourceCandidate]) -> list[DataChartSourceCandidate]:
    by_key: dict[tuple[str, str], DataChartSourceCandidate] = {}
    for candidate in candidates:
        key = (candidate.data_ref, candidate.provenance_ref)
        by_key.setdefault(key, candidate)
    return sorted(by_key.values(), key=lambda item: item.data_id)


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    normalized = normalized.strip("._-")
    return normalized or "unknown"


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


__all__ = [
    "DATA_BACKED_CHARTS_PHASE",
    "DATA_BACKED_CHARTS_SCHEMA_VERSION",
    "DataBackedChartResult",
    "DataChartBinding",
    "DataChartRequest",
    "DataChartSeries",
    "DataChartSourceCandidate",
    "bind_data_backed_charts",
    "sample_data_backed_chart_report",
]
