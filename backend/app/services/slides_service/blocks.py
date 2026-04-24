from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SlideBlockType(str, Enum):
    TEXT = "text_block"
    BULLET = "bullet_block"
    TABLE = "table_block"
    CHART = "chart_block"
    COMPARISON = "comparison_block"
    TIMELINE = "timeline_block"
    BUSINESS_METRIC = "business_metric_block"


class ChartType(str, Enum):
    BAR = "bar"


@dataclass(frozen=True)
class TextBlock:
    block_id: str
    text: str
    caption: str | None = None
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.TEXT)


@dataclass(frozen=True)
class BulletBlock:
    block_id: str
    bullets: tuple[str, ...]
    heading: str | None = None
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.BULLET)


@dataclass(frozen=True)
class TableBlock:
    block_id: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    caption: str | None = None
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.TABLE)


@dataclass(frozen=True)
class ChartBlock:
    block_id: str
    title: str
    categories: tuple[str, ...]
    values: tuple[float, ...]
    unit: str = ""
    chart_type: ChartType = ChartType.BAR
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.CHART)


@dataclass(frozen=True)
class ComparisonBlock:
    block_id: str
    left_title: str
    left_items: tuple[str, ...]
    right_title: str
    right_items: tuple[str, ...]
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.COMPARISON)


@dataclass(frozen=True)
class TimelineItem:
    label: str
    detail: str


@dataclass(frozen=True)
class TimelineBlock:
    block_id: str
    items: tuple[TimelineItem, ...]
    caption: str | None = None
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.TIMELINE)


@dataclass(frozen=True)
class BusinessMetric:
    label: str
    value: str
    note: str | None = None


@dataclass(frozen=True)
class BusinessMetricBlock:
    block_id: str
    metrics: tuple[BusinessMetric, ...]
    caption: str | None = None
    block_type: SlideBlockType = field(init=False, default=SlideBlockType.BUSINESS_METRIC)


SlideBlock = TextBlock | BulletBlock | TableBlock | ChartBlock | ComparisonBlock | TimelineBlock | BusinessMetricBlock
