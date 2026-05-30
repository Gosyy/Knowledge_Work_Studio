from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION = "presentation_template_brand_profile.v1"
TEMPLATE_BRAND_PROFILE_PHASE = "KR-7I template and brand understanding"
TEMPLATE_BRAND_PROFILE_SOURCE_KIND = "uploaded_pptx_template"

EMU_PER_INCH = 914_400
PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {"p": PML_NS, "a": DRAWING_NS, "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

PPTX_REQUIRED_PARTS = (
    "[Content_Types].xml",
    "ppt/presentation.xml",
)

FORBIDDEN_TEMPLATE_REFERENCE_PREFIXES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "ftp://",
    "file://",
    "//",
)

ROLE_TO_LAYOUT_FAMILY = {
    "cover": "cover",
    "title": "cover",
    "executive_summary": "title_content",
    "problem": "title_content",
    "insight": "title_content",
    "solution": "title_content",
    "roadmap": "timeline",
    "data": "data",
    "decision": "comparison",
    "closing": "closing",
}


@dataclass(frozen=True)
class TemplateSlideSize:
    width_emu: int
    height_emu: int
    width_inches: float
    height_inches: float
    aspect_ratio: float
    preset: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TemplateThemeProfile:
    theme_name: str | None
    major_font: str | None
    minor_font: str | None
    color_tokens: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "theme_name": self.theme_name,
            "major_font": self.major_font,
            "minor_font": self.minor_font,
            "color_tokens": dict(self.color_tokens),
        }


@dataclass(frozen=True)
class TemplateLayoutProfile:
    layout_id: str
    layout_name: str
    layout_family: str
    placeholder_types: tuple[str, ...]
    placeholder_count: int
    source_part: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["placeholder_types"] = list(self.placeholder_types)
        return payload


@dataclass(frozen=True)
class TemplateMediaAssetProfile:
    asset_id: str
    source_part: str
    extension: str
    checksum_sha256: str
    size_bytes: int
    width_px: int | None
    height_px: int | None
    asset_role_hint: str
    reused_as_generated_asset: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TemplateBrandProfileResult:
    schema_version: str
    phase: str
    status: str
    template_source_kind: str
    template_id: str
    template_file_name: str
    slide_size: TemplateSlideSize | None
    theme: TemplateThemeProfile | None
    slide_masters_count: int
    slide_layouts: tuple[TemplateLayoutProfile, ...]
    media_assets: tuple[TemplateMediaAssetProfile, ...]
    role_layout_family_map: dict[str, str]
    unsupported_features: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    template_profile_built: bool
    template_style_understanding_implemented: bool
    template_content_copied: bool
    production_layout_engine_implemented: bool
    renderer_runtime_changed: bool
    visual_qa_executed: bool
    kimi_level_quality_claimed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "status": self.status,
            "template_source_kind": self.template_source_kind,
            "template_id": self.template_id,
            "template_file_name": self.template_file_name,
            "slide_size": self.slide_size.as_dict() if self.slide_size else None,
            "theme": self.theme.as_dict() if self.theme else None,
            "slide_masters_count": self.slide_masters_count,
            "slide_layout_count": len(self.slide_layouts),
            "slide_layouts": [layout.as_dict() for layout in self.slide_layouts],
            "media_asset_count": len(self.media_assets),
            "media_assets": [asset.as_dict() for asset in self.media_assets],
            "role_layout_family_map": dict(self.role_layout_family_map),
            "unsupported_features": list(self.unsupported_features),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "template_profile_built": self.template_profile_built,
            "template_style_understanding_implemented": self.template_style_understanding_implemented,
            "template_content_copied": self.template_content_copied,
            "production_layout_engine_implemented": self.production_layout_engine_implemented,
            "renderer_runtime_changed": self.renderer_runtime_changed,
            "visual_qa_executed": self.visual_qa_executed,
            "kimi_level_quality_claimed": self.kimi_level_quality_claimed,
            "non_goals": [
                "no_template_clone_rewrite_mode",
                "no_blind_copying_old_template_text",
                "no_production_layout_engine",
                "no_renderer_runtime_changes",
                "no_visual_qa_scoring",
                "no_kimi_level_quality_claim",
                "no_ui_changes",
                "no_gigachat_runtime_changes",
            ],
        }


def validate_template_reference(reference: str) -> list[str]:
    value = (reference or "").strip()
    if not value:
        return ["template reference is required"]
    normalized = value.lower()
    errors: list[str] = []
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_TEMPLATE_REFERENCE_PREFIXES) or "://" in normalized:
        errors.append("external template references are forbidden for KR-7I template profile inspection")
    if ".." in value or value.startswith(("/", "\\")):
        errors.append("template references must not be absolute paths or path traversal strings")
    return errors


def inspect_pptx_template_brand_profile(
    pptx_path: str | Path,
    *,
    template_id: str = "uploaded_template_profile",
) -> TemplateBrandProfileResult:
    path = Path(pptx_path)
    errors = validate_template_reference(path.name)
    if not path.exists():
        errors.append(f"template file is missing: {path}")
        return _result(template_id=template_id, template_file_name=path.name, errors=errors)
    try:
        data = path.read_bytes()
    except OSError as exc:
        errors.append(f"cannot read template file: {exc}")
        return _result(template_id=template_id, template_file_name=path.name, errors=errors)
    return inspect_pptx_template_brand_profile_bytes(data, template_id=template_id, template_file_name=path.name)


def inspect_pptx_template_brand_profile_bytes(
    pptx_bytes: bytes,
    *,
    template_id: str = "uploaded_template_profile",
    template_file_name: str = "uploaded-template.pptx",
) -> TemplateBrandProfileResult:
    errors: list[str] = validate_template_reference(template_file_name)
    warnings: list[str] = []
    unsupported_features: list[str] = []

    try:
        with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as pptx:
            names = set(pptx.namelist())
            missing = [part for part in PPTX_REQUIRED_PARTS if part not in names]
            if missing:
                errors.extend(f"missing required PPTX part: {part}" for part in missing)
                return _result(template_id=template_id, template_file_name=template_file_name, errors=errors)

            slide_size = _parse_slide_size(_read_xml(pptx, "ppt/presentation.xml"), errors)
            theme = _parse_theme_profile(pptx, names, warnings)
            masters_count = len([name for name in names if name.startswith("ppt/slideMasters/slideMaster") and name.endswith(".xml")])
            if masters_count == 0:
                errors.append("template must contain at least one slide master")
            slide_layouts = _parse_slide_layouts(pptx, names, warnings)
            if not slide_layouts:
                errors.append("template must contain at least one slide layout")
            media_assets = _parse_media_assets(pptx, names, warnings)
            unsupported_features.extend(_detect_unsupported_features(pptx, names))
    except zipfile.BadZipFile:
        errors.append("template file is not a valid PPTX/ZIP container")
        return _result(template_id=template_id, template_file_name=template_file_name, errors=errors)

    if theme is None:
        errors.append("template must contain a parseable theme profile")
    if not media_assets:
        warnings.append("template contains no reusable media assets; generated deck must remain typographic or diagrammatic")

    return _result(
        template_id=template_id,
        template_file_name=template_file_name,
        errors=errors,
        warnings=warnings,
        unsupported_features=unsupported_features,
        slide_size=slide_size,
        theme=theme,
        slide_masters_count=masters_count,
        slide_layouts=slide_layouts,
        media_assets=media_assets,
    )


def sample_template_brand_profile_report() -> dict[str, Any]:
    return inspect_pptx_template_brand_profile_bytes(
        build_sample_template_pptx_bytes(),
        template_id="kr7i_sample_template",
        template_file_name="kr7i-sample-template.pptx",
    ).as_dict()


def build_sample_template_pptx_bytes() -> bytes:
    media = _sample_png_bytes()
    files = {
        "[Content_Types].xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Default Extension='png' ContentType='image/png'/>
  <Override PartName='/ppt/presentation.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'/>
  <Override PartName='/ppt/theme/theme1.xml' ContentType='application/vnd.openxmlformats-officedocument.theme+xml'/>
  <Override PartName='/ppt/slideMasters/slideMaster1.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'/>
  <Override PartName='/ppt/slideLayouts/slideLayout1.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'/>
  <Override PartName='/ppt/slideLayouts/slideLayout2.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'/>
  <Override PartName='/ppt/slideLayouts/slideLayout3.xml' ContentType='application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'/>
</Types>""",
        "ppt/presentation.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:presentation xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main' xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
  <p:sldSz cx='12192000' cy='6858000' type='wide'/>
</p:presentation>""",
        "ppt/theme/theme1.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<a:theme xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main' name='KR7I Sample Brand'>
  <a:themeElements>
    <a:clrScheme name='KR7I Sample Colors'>
      <a:dk1><a:srgbClr val='111827'/></a:dk1>
      <a:lt1><a:srgbClr val='F8FAFC'/></a:lt1>
      <a:accent1><a:srgbClr val='2563EB'/></a:accent1>
      <a:accent2><a:srgbClr val='14B8A6'/></a:accent2>
      <a:accent3><a:srgbClr val='F97316'/></a:accent3>
    </a:clrScheme>
    <a:fontScheme name='KR7I Sample Fonts'>
      <a:majorFont><a:latin typeface='Aptos Display'/></a:majorFont>
      <a:minorFont><a:latin typeface='Aptos'/></a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>""",
        "ppt/slideMasters/slideMaster1.xml": """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:sldMaster xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'>
  <p:cSld><p:bg/></p:cSld>
</p:sldMaster>""",
        "ppt/slideLayouts/slideLayout1.xml": _layout_xml("Title Slide", ("ctrTitle", "subTitle")),
        "ppt/slideLayouts/slideLayout2.xml": _layout_xml("Title and Content", ("title", "body")),
        "ppt/slideLayouts/slideLayout3.xml": _layout_xml("Comparison", ("title", "body", "body")),
        "ppt/media/image1.png": media,
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as pptx:
        for name, content in files.items():
            pptx.writestr(name, content)
    return output.getvalue()


def _layout_xml(layout_name: str, placeholder_types: tuple[str, ...]) -> str:
    shapes = []
    for index, placeholder_type in enumerate(placeholder_types, start=1):
        shapes.append(
            """
      <p:sp>
        <p:nvSpPr><p:cNvPr id='{id}' name='{name}'/><p:cNvSpPr/><p:nvPr><p:ph type='{ph}' idx='{idx}'/></p:nvPr></p:nvSpPr>
        <p:spPr/>
      </p:sp>""".format(id=index, name=f"{layout_name} placeholder {index}", ph=placeholder_type, idx=index)
        )
    return """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<p:sldLayout xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main' type='obj' preserve='1'>
  <p:cSld name='{layout_name}'><p:spTree>{shapes}
  </p:spTree></p:cSld>
</p:sldLayout>""".format(layout_name=layout_name, shapes="".join(shapes))


def _sample_png_bytes() -> bytes:
    # 1x1 transparent PNG. The profile parser uses the PNG header only.
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C63600000020001E221BC330000000049454E44AE426082"
    )


def _read_xml(pptx: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(pptx.read(part))


def _parse_slide_size(root: ET.Element, errors: list[str]) -> TemplateSlideSize | None:
    node = root.find("p:sldSz", NS)
    if node is None:
        errors.append("presentation.xml is missing p:sldSz")
        return None
    try:
        width_emu = int(node.attrib.get("cx", "0"))
        height_emu = int(node.attrib.get("cy", "0"))
    except ValueError:
        errors.append("p:sldSz cx/cy must be integers")
        return None
    if width_emu <= 0 or height_emu <= 0:
        errors.append("p:sldSz cx/cy must be positive")
        return None
    width_inches = round(width_emu / EMU_PER_INCH, 4)
    height_inches = round(height_emu / EMU_PER_INCH, 4)
    return TemplateSlideSize(
        width_emu=width_emu,
        height_emu=height_emu,
        width_inches=width_inches,
        height_inches=height_inches,
        aspect_ratio=round(width_inches / height_inches, 4),
        preset=node.attrib.get("type"),
    )


def _parse_theme_profile(pptx: zipfile.ZipFile, names: set[str], warnings: list[str]) -> TemplateThemeProfile | None:
    theme_parts = sorted(name for name in names if name.startswith("ppt/theme/theme") and name.endswith(".xml"))
    if not theme_parts:
        warnings.append("template has no theme XML part")
        return None
    root = _read_xml(pptx, theme_parts[0])
    colors: dict[str, str] = {}
    for color_node in root.findall(".//a:clrScheme/*", NS):
        token = _strip_ns(color_node.tag)
        srgb = color_node.find(".//a:srgbClr", NS)
        if srgb is not None and srgb.attrib.get("val"):
            colors[token] = "#" + srgb.attrib["val"].upper()
    major_font = _first_font(root, ".//a:majorFont/a:latin")
    minor_font = _first_font(root, ".//a:minorFont/a:latin")
    return TemplateThemeProfile(
        theme_name=root.attrib.get("name"),
        major_font=major_font,
        minor_font=minor_font,
        color_tokens=colors,
    )


def _first_font(root: ET.Element, pattern: str) -> str | None:
    node = root.find(pattern, NS)
    if node is None:
        return None
    return node.attrib.get("typeface") or None


def _parse_slide_layouts(pptx: zipfile.ZipFile, names: set[str], warnings: list[str]) -> tuple[TemplateLayoutProfile, ...]:
    layouts: list[TemplateLayoutProfile] = []
    for index, part in enumerate(sorted(name for name in names if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml")), start=1):
        try:
            root = _read_xml(pptx, part)
        except ET.ParseError:
            warnings.append(f"cannot parse slide layout XML: {part}")
            continue
        c_sld = root.find("p:cSld", NS)
        layout_name = c_sld.attrib.get("name") if c_sld is not None else None
        layout_name = layout_name or f"layout_{index}"
        placeholders = tuple(_placeholder_type(node) for node in root.findall(".//p:ph", NS))
        placeholder_types = tuple(sorted(placeholders))
        layouts.append(
            TemplateLayoutProfile(
                layout_id=f"layout_{index:03d}",
                layout_name=layout_name,
                layout_family=_infer_layout_family(layout_name, placeholder_types),
                placeholder_types=placeholder_types,
                placeholder_count=len(placeholder_types),
                source_part=part,
            )
        )
    return tuple(layouts)


def _placeholder_type(node: ET.Element) -> str:
    return node.attrib.get("type") or "body"


def _infer_layout_family(layout_name: str, placeholder_types: tuple[str, ...]) -> str:
    lowered = layout_name.lower()
    placeholder_set = set(placeholder_types)
    if "title" in lowered and ("ctrTitle" in placeholder_set or "subTitle" in placeholder_set):
        return "cover"
    if "comparison" in lowered or len([item for item in placeholder_types if item == "body"]) >= 2:
        return "comparison"
    if "timeline" in lowered or "roadmap" in lowered:
        return "timeline"
    if "data" in lowered or "chart" in lowered or "table" in lowered:
        return "data"
    if "closing" in lowered or "conclusion" in lowered:
        return "closing"
    if "title" in lowered or "title" in placeholder_set:
        return "title_content"
    return "general_content"


def _parse_media_assets(pptx: zipfile.ZipFile, names: set[str], warnings: list[str]) -> tuple[TemplateMediaAssetProfile, ...]:
    assets: list[TemplateMediaAssetProfile] = []
    for index, part in enumerate(sorted(name for name in names if name.startswith("ppt/media/") and not name.endswith("/")), start=1):
        data = pptx.read(part)
        width, height = _image_dimensions(data)
        if width is None or height is None:
            warnings.append(f"cannot determine media dimensions: {part}")
        extension = Path(part).suffix.lower().lstrip(".") or "unknown"
        assets.append(
            TemplateMediaAssetProfile(
                asset_id=f"template_asset_{index:03d}",
                source_part=part,
                extension=extension,
                checksum_sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
                width_px=width,
                height_px=height,
                asset_role_hint="template_media_asset",
            )
        )
    return tuple(assets)


def _image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        return _jpeg_dimensions(data)
    return None, None


def _jpeg_dimensions(data: bytes) -> tuple[int | None, int | None]:
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break
        segment_length = int.from_bytes(data[index : index + 2], "big")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if index + 7 <= len(data):
                height = int.from_bytes(data[index + 3 : index + 5], "big")
                width = int.from_bytes(data[index + 5 : index + 7], "big")
                return width, height
        index += max(segment_length, 2)
    return None, None


def _detect_unsupported_features(pptx: zipfile.ZipFile, names: set[str]) -> list[str]:
    unsupported: set[str] = set()
    for part in sorted(name for name in names if name.startswith("ppt/") and name.endswith(".xml")):
        try:
            text = pptx.read(part).decode("utf-8", errors="ignore")
        except OSError:
            continue
        if "<p:video" in text or "<p14:media" in text:
            unsupported.add("video_or_embedded_media")
        if "<p:oleObj" in text:
            unsupported.add("ole_objects")
        if "<p:extLst" in text:
            unsupported.add("extended_vendor_features")
        if "<p:anim" in text or "<p:timing" in text:
            unsupported.add("animations_or_timing")
    return sorted(unsupported)


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _result(
    *,
    template_id: str,
    template_file_name: str,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    unsupported_features: list[str] | None = None,
    slide_size: TemplateSlideSize | None = None,
    theme: TemplateThemeProfile | None = None,
    slide_masters_count: int = 0,
    slide_layouts: tuple[TemplateLayoutProfile, ...] = (),
    media_assets: tuple[TemplateMediaAssetProfile, ...] = (),
) -> TemplateBrandProfileResult:
    errors_tuple = tuple(errors or ())
    ready = not errors_tuple
    return TemplateBrandProfileResult(
        schema_version=TEMPLATE_BRAND_PROFILE_SCHEMA_VERSION,
        phase=TEMPLATE_BRAND_PROFILE_PHASE,
        status="ready" if ready else "blocked",
        template_source_kind=TEMPLATE_BRAND_PROFILE_SOURCE_KIND,
        template_id=template_id,
        template_file_name=template_file_name,
        slide_size=slide_size,
        theme=theme,
        slide_masters_count=slide_masters_count,
        slide_layouts=slide_layouts,
        media_assets=media_assets,
        role_layout_family_map=dict(ROLE_TO_LAYOUT_FAMILY),
        unsupported_features=tuple(sorted(unsupported_features or ())),
        warnings=tuple(warnings or ()),
        errors=errors_tuple,
        template_profile_built=ready,
        template_style_understanding_implemented=ready,
        template_content_copied=False,
        production_layout_engine_implemented=False,
        renderer_runtime_changed=False,
        visual_qa_executed=False,
        kimi_level_quality_claimed=False,
    )
