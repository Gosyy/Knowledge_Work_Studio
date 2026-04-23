from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.slides_service.outline import PlannedSlide, SlideType


@dataclass(frozen=True)
class ShapeBox:
    x: int
    y: int
    cx: int
    cy: int


@dataclass(frozen=True)
class ImagePlaceholderBox:
    placeholder_id: str
    x: int
    y: int
    cx: int
    cy: int


@dataclass(frozen=True)
class SlideLayoutSpec:
    layout_id: str
    title_box: ShapeBox
    body_boxes: tuple[ShapeBox, ...]
    title_size: int
    body_size: int
    title_bold: bool = True
    title_align: str = "left"
    body_align: str = "left"
    image_placeholders: tuple[ImagePlaceholderBox, ...] = ()


@dataclass(frozen=True)
class SlideTemplate:
    template_id: str
    display_name: str
    theme_name: str
    background_color: str
    title_color: str
    body_color: str
    accent_color: str
    font_family: str
    layouts: dict[str, SlideLayoutSpec]


@dataclass(frozen=True)
class ResolvedSlideLayout:
    template: SlideTemplate
    layout: SlideLayoutSpec


def get_template_registry() -> dict[str, SlideTemplate]:
    return {
        "default_light": SlideTemplate(
            template_id="default_light",
            display_name="Default Light",
            theme_name="KW Studio Light",
            background_color="FFFFFF",
            title_color="1F1F1F",
            body_color="333333",
            accent_color="4472C4",
            font_family="Arial",
            layouts=_build_layouts(),
        ),
        "default_dark": SlideTemplate(
            template_id="default_dark",
            display_name="Default Dark",
            theme_name="KW Studio Dark",
            background_color="1F1F1F",
            title_color="FFFFFF",
            body_color="F2F2F2",
            accent_color="5B9BD5",
            font_family="Arial",
            layouts=_build_layouts(),
        ),
        "business_clean": SlideTemplate(
            template_id="business_clean",
            display_name="Business Clean",
            theme_name="KW Studio Business",
            background_color="F7F9FC",
            title_color="12324A",
            body_color="30485E",
            accent_color="2F75B5",
            font_family="Aptos",
            layouts=_build_layouts(),
        ),
    }


def get_template(template_id: str) -> SlideTemplate:
    registry = get_template_registry()
    try:
        return registry[template_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported slide template: {template_id}") from exc


def resolve_layout_for_slide(slide: PlannedSlide, *, template_id: str = "default_light") -> ResolvedSlideLayout:
    template = get_template(template_id)
    layout_id = slide.layout_hint or _default_layout_for_type(slide.slide_type)
    try:
        layout = template.layouts[layout_id]
    except KeyError as exc:
        raise ValueError(f"Template '{template_id}' does not define layout '{layout_id}'") from exc
    return ResolvedSlideLayout(template=template, layout=layout)


def _build_layouts() -> dict[str, SlideLayoutSpec]:
    return {
        "title_slide": SlideLayoutSpec(
            layout_id="title_slide",
            title_box=ShapeBox(685800, 777240, 7772400, 1143000),
            body_boxes=(ShapeBox(1143000, 2148840, 6858000, 1143000),),
            title_size=3600,
            body_size=2200,
            title_align="center",
            body_align="center",
        ),
        "section_slide": SlideLayoutSpec(
            layout_id="section_slide",
            title_box=ShapeBox(685800, 1028700, 7772400, 914400),
            body_boxes=(ShapeBox(1371600, 2286000, 6400800, 1371600),),
            title_size=3000,
            body_size=2200,
            title_align="center",
            body_align="center",
        ),
        "title_and_bullets": SlideLayoutSpec(
            layout_id="title_and_bullets",
            title_box=ShapeBox(457200, 274320, 8229600, 914400),
            body_boxes=(ShapeBox(685800, 1371600, 7772400, 4572000),),
            title_size=3000,
            body_size=2000,
        ),
        "two_column_comparison": SlideLayoutSpec(
            layout_id="two_column_comparison",
            title_box=ShapeBox(457200, 274320, 8229600, 914400),
            body_boxes=(
                ShapeBox(685800, 1371600, 3429000, 4114800),
                ShapeBox(4343400, 1371600, 3429000, 4114800),
            ),
            title_size=3000,
            body_size=1900,
        ),
        "timeline": SlideLayoutSpec(
            layout_id="timeline",
            title_box=ShapeBox(457200, 274320, 8229600, 914400),
            body_boxes=(ShapeBox(914400, 1600200, 7315200, 4114800),),
            title_size=3000,
            body_size=1900,
        ),
        "data_summary": SlideLayoutSpec(
            layout_id="data_summary",
            title_box=ShapeBox(457200, 274320, 8229600, 914400),
            body_boxes=(ShapeBox(914400, 1485900, 7315200, 4343400),),
            title_size=3000,
            body_size=1800,
        ),
        "conclusion": SlideLayoutSpec(
            layout_id="conclusion",
            title_box=ShapeBox(685800, 731520, 7772400, 1028700),
            body_boxes=(ShapeBox(1143000, 2057400, 6858000, 1828800),),
            title_size=3200,
            body_size=2100,
            title_align="center",
            body_align="center",
        ),
        "content_with_visual": SlideLayoutSpec(
            layout_id="content_with_visual",
            title_box=ShapeBox(457200, 274320, 8229600, 914400),
            body_boxes=(ShapeBox(685800, 1371600, 3429000, 4114800),),
            image_placeholders=(ImagePlaceholderBox("primary_visual", 4343400, 1371600, 3429000, 4114800),),
            title_size=3000,
            body_size=1900,
        ),
        "title_with_visual": SlideLayoutSpec(
            layout_id="title_with_visual",
            title_box=ShapeBox(685800, 548640, 7772400, 914400),
            body_boxes=(ShapeBox(1143000, 4800600, 6858000, 685800),),
            image_placeholders=(ImagePlaceholderBox("hero_visual", 1600200, 1600200, 5943600, 2743200),),
            title_size=3400,
            body_size=2000,
            title_align="center",
            body_align="center",
        ),
    }


def _default_layout_for_type(slide_type: SlideType) -> str:
    if slide_type is SlideType.TITLE:
        return "title_slide"
    if slide_type in {SlideType.SECTION, SlideType.APPENDIX}:
        return "section_slide"
    if slide_type is SlideType.COMPARISON:
        return "two_column_comparison"
    if slide_type is SlideType.TIMELINE:
        return "timeline"
    if slide_type is SlideType.DATA:
        return "data_summary"
    if slide_type is SlideType.CONCLUSION:
        return "conclusion"
    return "title_and_bullets"
