from __future__ import annotations

from dataclasses import dataclass
from html import escape
import io
import zipfile

from backend.app.services.slides_service.layouts import ImagePlaceholderBox, ResolvedSlideLayout, ShapeBox, SlideLayoutSpec, SlideTemplate, get_template, resolve_layout_for_slide
from backend.app.services.slides_service.media import ImageFitMode, SlideMediaAsset
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideOutlineItem, SlideType, StoryArcStage

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


@dataclass(frozen=True)
class PreparedSlideMedia:
    rel_id: str
    media_path: str
    asset: SlideMediaAsset
    placeholder: ImagePlaceholderBox
    render_box: ShapeBox
    src_rect_xml: str
    caption_box: ShapeBox | None = None


def generate_pptx_from_plan(plan: PresentationPlan, *, template_id: str = "default_light") -> bytes:
    template = get_template(template_id)
    media_extensions = _collect_media_extensions(plan)
    buffer = io.BytesIO()
    media_counter = 1
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", _content_types_xml(len(plan.slides), media_extensions=media_extensions))
        pptx.writestr("_rels/.rels", _root_relationships_xml())
        pptx.writestr("docProps/core.xml", _core_properties_xml(plan.deck_title))
        pptx.writestr("docProps/app.xml", _app_properties_xml(len(plan.slides)))
        pptx.writestr("ppt/presentation.xml", _presentation_xml(len(plan.slides)))
        pptx.writestr("ppt/_rels/presentation.xml.rels", _presentation_relationships_xml(len(plan.slides)))
        pptx.writestr("ppt/theme/theme1.xml", _theme_xml(template))
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", _slide_master_xml(template))
        pptx.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", _slide_master_relationships_xml())
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", _slide_layout_xml())
        pptx.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", _slide_layout_relationships_xml())
        for index, slide in enumerate(plan.slides, start=1):
            resolved_layout = resolve_layout_for_slide(slide, template_id=template.template_id)
            prepared_media, media_counter = _prepare_slide_media(slide=slide, resolved_layout=resolved_layout, media_counter=media_counter)
            for item in prepared_media:
                pptx.writestr(item.media_path, item.asset.data)
            pptx.writestr(
                f"ppt/slides/slide{index}.xml",
                _slide_xml(slide, index=index, resolved_layout=resolved_layout, prepared_media=prepared_media),
            )
            pptx.writestr(
                f"ppt/slides/_rels/slide{index}.xml.rels",
                _slide_relationships_xml(prepared_media),
            )
    return buffer.getvalue()


def generate_pptx_from_outline(outline: tuple[SlideOutlineItem, ...]) -> bytes:
    plan = _outline_to_plan(outline)
    return generate_pptx_from_plan(plan, template_id="default_light")


def _outline_to_plan(outline: tuple[SlideOutlineItem, ...]) -> PresentationPlan:
    if not outline:
        outline = (SlideOutlineItem(title="Untitled presentation", bullets=("No content",)),)
    slides: list[PlannedSlide] = []
    for index, item in enumerate(outline, start=1):
        if index == 1:
            slide_type = SlideType.TITLE
            stage = StoryArcStage.OPENING
            layout_hint = "title_slide"
        elif index == len(outline):
            slide_type = SlideType.CONCLUSION
            stage = StoryArcStage.CLOSE
            layout_hint = "conclusion"
        else:
            slide_type = SlideType.CONTENT
            stage = StoryArcStage.ANALYSIS
            layout_hint = "title_and_bullets"
        slides.append(
            PlannedSlide(
                slide_id=f"outline_{index:03d}",
                slide_type=slide_type,
                story_arc_stage=stage,
                title=item.title,
                bullets=item.bullets,
                speaker_notes=None,
                layout_hint=layout_hint,
            )
        )
    return PresentationPlan(
        deck_title=slides[0].title,
        deck_goal="Compatibility render from outline.",
        audience="general_business",
        tone="clear_professional",
        target_slide_count=len(slides),
        story_arc=tuple(slide.story_arc_stage for slide in slides),
        slides=tuple(slides),
    )


def _collect_media_extensions(plan: PresentationPlan) -> set[str]:
    extensions: set[str] = set()
    for slide in plan.slides:
        for asset in slide.media_assets:
            extensions.add(asset.extension())
    return extensions


def _prepare_slide_media(*, slide: PlannedSlide, resolved_layout: ResolvedSlideLayout, media_counter: int) -> tuple[tuple[PreparedSlideMedia, ...], int]:
    assets = slide.media_assets
    if not assets:
        return (), media_counter

    placeholders = resolved_layout.layout.image_placeholders
    if not placeholders:
        raise ValueError(
            f"Layout '{resolved_layout.layout.layout_id}' does not define image placeholders for slide '{slide.slide_id}'."
        )
    if len(assets) > len(placeholders):
        raise ValueError(
            f"Slide '{slide.slide_id}' has {len(assets)} media asset(s) but layout '{resolved_layout.layout.layout_id}' only provides {len(placeholders)} placeholder(s)."
        )

    prepared: list[PreparedSlideMedia] = []
    next_counter = media_counter
    for offset, (asset, placeholder) in enumerate(zip(assets, placeholders, strict=False), start=0):
        extension = asset.extension()
        media_filename = f"image{next_counter}.{extension}"
        media_path = f"ppt/media/{media_filename}"
        rel_id = f"rId{offset + 2}"
        render_box, src_rect_xml, caption_box = _resolve_media_box(asset=asset, placeholder=placeholder)
        prepared.append(
            PreparedSlideMedia(
                rel_id=rel_id,
                media_path=media_path,
                asset=asset,
                placeholder=placeholder,
                render_box=render_box,
                src_rect_xml=src_rect_xml,
                caption_box=caption_box,
            )
        )
        next_counter += 1
    return tuple(prepared), next_counter


def _resolve_media_box(*, asset: SlideMediaAsset, placeholder: ImagePlaceholderBox) -> tuple[ShapeBox, str, ShapeBox | None]:
    width_px, height_px = asset.normalized_dimensions()
    asset_ratio = width_px / height_px
    caption_box = _caption_box_for_asset(asset=asset, placeholder=placeholder)
    image_area = _image_area_without_caption(placeholder=placeholder, caption_box=caption_box)
    placeholder_ratio = image_area.cx / image_area.cy

    if asset.fit_mode is ImageFitMode.STRETCH:
        return ShapeBox(image_area.x, image_area.y, image_area.cx, image_area.cy), "", caption_box

    if asset.fit_mode is ImageFitMode.COVER:
        src_rect_xml = _src_rect_for_cover(asset_ratio=asset_ratio, placeholder_ratio=placeholder_ratio)
        return ShapeBox(image_area.x, image_area.y, image_area.cx, image_area.cy), src_rect_xml, caption_box

    # contain
    if asset_ratio >= placeholder_ratio:
        render_cx = image_area.cx
        render_cy = max(1, round(image_area.cx / asset_ratio))
        render_x = image_area.x
        render_y = image_area.y + max(0, (image_area.cy - render_cy) // 2)
    else:
        render_cy = image_area.cy
        render_cx = max(1, round(image_area.cy * asset_ratio))
        render_x = image_area.x + max(0, (image_area.cx - render_cx) // 2)
        render_y = image_area.y
    return ShapeBox(render_x, render_y, render_cx, render_cy), "", caption_box


def _caption_box_for_asset(*, asset: SlideMediaAsset, placeholder: ImagePlaceholderBox) -> ShapeBox | None:
    if not asset.caption and not asset.source_label:
        return None
    caption_height = max(274320, placeholder.cy // 5)
    return ShapeBox(placeholder.x, placeholder.y + placeholder.cy - caption_height, placeholder.cx, caption_height)


def _image_area_without_caption(*, placeholder: ImagePlaceholderBox, caption_box: ShapeBox | None) -> ShapeBox:
    if caption_box is None:
        return ShapeBox(placeholder.x, placeholder.y, placeholder.cx, placeholder.cy)
    image_cy = max(1, caption_box.y - placeholder.y - 114300)
    return ShapeBox(placeholder.x, placeholder.y, placeholder.cx, image_cy)


def _src_rect_for_cover(*, asset_ratio: float, placeholder_ratio: float) -> str:
    if asset_ratio == placeholder_ratio:
        return ""
    if asset_ratio > placeholder_ratio:
        visible_fraction = placeholder_ratio / asset_ratio
        crop_each_side = max(0.0, (1.0 - visible_fraction) / 2.0)
        amount = min(100000, max(0, round(crop_each_side * 100000)))
        return f'<a:srcRect l="{amount}" r="{amount}"/>'
    visible_fraction = asset_ratio / placeholder_ratio
    crop_each_side = max(0.0, (1.0 - visible_fraction) / 2.0)
    amount = min(100000, max(0, round(crop_each_side * 100000)))
    return f'<a:srcRect t="{amount}" b="{amount}"/>'


def _content_types_xml(slide_count: int, *, media_extensions: set[str]) -> str:
    slide_overrides = "\n".join(
        f'  <Override PartName="/ppt/slides/slide{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for index in range(1, slide_count + 1)
    )
    media_defaults = "\n".join(_media_default_xml(extension) for extension in sorted(media_extensions))
    media_defaults_block = f"\n{media_defaults}" if media_defaults else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>{media_defaults_block}
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
{slide_overrides}
</Types>
'''


def _media_default_xml(extension: str) -> str:
    if extension == "png":
        content_type = "image/png"
    elif extension == "jpg":
        content_type = "image/jpeg"
    elif extension == "gif":
        content_type = "image/gif"
    else:
        raise ValueError(f"Unsupported media extension: {extension}")
    return f'  <Default Extension="{extension}" ContentType="{content_type}"/>'


def _root_relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
'''


def _presentation_relationships_xml(slide_count: int) -> str:
    relationships = [
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    for index in range(1, slide_count + 1):
        relationships.append(
            f'  <Relationship Id="rId{index + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{index}.xml"/>'
        )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{chr(10).join(relationships)}
</Relationships>
'''


def _presentation_xml(slide_count: int) -> str:
    slide_ids = "\n".join(
        f'    <p:sldId id="{255 + index}" r:id="rId{index + 1}"/>'
        for index in range(1, slide_count + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>
{slide_ids}
  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>
'''


def _slide_xml(slide: PlannedSlide, *, index: int, resolved_layout: ResolvedSlideLayout, prepared_media: tuple[PreparedSlideMedia, ...]) -> str:
    template = resolved_layout.template
    layout = resolved_layout.layout
    title = _xml_text(slide.title)
    body_boxes_xml = _body_boxes_xml(slide=slide, layout=layout, template=template, index=index)
    media_xml = _picture_shapes_xml(prepared_media=prepared_media, index=index, template=template)
    title_box = layout.title_box
    title_alignment = "ctr" if layout.title_align == "center" else "l"
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="{template.background_color}"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{index * 10 + 1}" name="Title {index}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{title_box.x}" y="{title_box.y}"/><a:ext cx="{title_box.cx}" cy="{title_box.cy}"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="{title_alignment}"/><a:r><a:rPr lang="en-US" sz="{layout.title_size}" b="{1 if layout.title_bold else 0}"><a:solidFill><a:srgbClr val="{template.title_color}"/></a:solidFill><a:latin typeface="{template.font_family}"/></a:rPr><a:t>{title}</a:t></a:r></a:p></p:txBody>
      </p:sp>
{body_boxes_xml}
{media_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
'''


def _body_boxes_xml(*, slide: PlannedSlide, layout: SlideLayoutSpec, template: SlideTemplate, index: int) -> str:
    if len(layout.body_boxes) == 2:
        midpoint = max(1, (len(slide.bullets) + 1) // 2)
        bullet_groups = (slide.bullets[:midpoint], slide.bullets[midpoint:] or ("No secondary comparison point",))
    else:
        bullet_groups = (slide.bullets,)

    body_xml: list[str] = []
    for offset, (box, bullets) in enumerate(zip(layout.body_boxes, bullet_groups, strict=False), start=2):
        alignment = "ctr" if layout.body_align == "center" else "l"
        bullet_paragraphs = "\n".join(
            _bullet_paragraph_xml(
                text=bullet,
                font_size=layout.body_size,
                color=template.body_color,
                font_family=template.font_family,
                alignment=alignment,
                accent_color=template.accent_color,
            )
            for bullet in bullets
        )
        body_xml.append(
            f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{index * 10 + offset}" name="Content {index}-{offset}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="{offset - 1}"/></p:nvPr></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.cx}" cy="{box.cy}"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/>
{bullet_paragraphs}
        </p:txBody>
      </p:sp>'''
        )
    return "\n".join(body_xml)


def _picture_shapes_xml(*, prepared_media: tuple[PreparedSlideMedia, ...], index: int, template: SlideTemplate) -> str:
    xml: list[str] = []
    for offset, item in enumerate(prepared_media, start=1):
        alt_text = _xml_text(item.asset.alt_text or item.asset.filename)
        src_rect = item.src_rect_xml or ""
        xml.append(
            f'''      <p:pic>
        <p:nvPicPr>
          <p:cNvPr id="{index * 100 + offset}" name="Picture {index}-{offset}" descr="{alt_text}"/>
          <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
          <p:nvPr/>
        </p:nvPicPr>
        <p:blipFill>
          <a:blip r:embed="{item.rel_id}"/>
          {src_rect}
          <a:stretch><a:fillRect/></a:stretch>
        </p:blipFill>
        <p:spPr>
          <a:xfrm><a:off x="{item.render_box.x}" y="{item.render_box.y}"/><a:ext cx="{item.render_box.cx}" cy="{item.render_box.cy}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
      </p:pic>'''
        )
    for offset, item in enumerate(prepared_media, start=1):
        if item.caption_box is None:
            continue
        caption_lines = [part for part in (item.asset.caption, item.asset.source_label) if part]
        if not caption_lines:
            continue
        caption_text = " • ".join(_xml_text(part) for part in caption_lines)
        xml.append(
            f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{index * 100 + 50 + offset}" name="Caption {index}-{offset}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{item.caption_box.x}" y="{item.caption_box.y}"/><a:ext cx="{item.caption_box.cx}" cy="{item.caption_box.cy}"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="en-US" sz="1200"><a:solidFill><a:srgbClr val="{template.body_color}"/></a:solidFill><a:latin typeface="{template.font_family}"/></a:rPr><a:t>{caption_text}</a:t></a:r></a:p></p:txBody>
      </p:sp>'''
        )
    return "\n".join(xml)


def _bullet_paragraph_xml(*, text: str, font_size: int, color: str, font_family: str, alignment: str, accent_color: str) -> str:
    return (
        '          <a:p><a:pPr lvl="0" algn="{alignment}"><a:buChar char="•"/><a:defRPr sz="{font_size}"><a:solidFill><a:srgbClr val="{accent_color}"/></a:solidFill></a:defRPr></a:pPr>'
        '<a:r><a:rPr lang="en-US" sz="{font_size}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font_family}"/></a:rPr><a:t>{text}</a:t></a:r></a:p>'
    ).format(alignment=alignment, font_size=font_size, color=color, font_family=font_family, accent_color=accent_color, text=_xml_text(text))


def _slide_relationships_xml(prepared_media: tuple[PreparedSlideMedia, ...]) -> str:
    relationships = [
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    ]
    relationships.extend(
        f'  <Relationship Id="{item.rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{item.media_path.rsplit("/", 1)[-1]}"/>'
        for item in prepared_media
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{chr(10).join(relationships)}
</Relationships>
'''


def _slide_master_relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
'''


def _slide_layout_relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
'''


def _slide_master_xml(template: SlideTemplate) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{template.background_color}"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>
'''


def _slide_layout_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}" type="titleAndContent" preserve="1">
  <p:cSld name="Title and Content"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
'''


def _theme_xml(template: SlideTemplate) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="{A_NS}" name="{template.theme_name}">
  <a:themeElements>
    <a:clrScheme name="{template.theme_name}">
      <a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="{template.title_color}"/></a:dk2><a:lt2><a:srgbClr val="{template.background_color}"/></a:lt2>
      <a:accent1><a:srgbClr val="{template.accent_color}"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
      <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4>
      <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6>
      <a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="{template.theme_name}"><a:majorFont><a:latin typeface="{template.font_family}"/></a:majorFont><a:minorFont><a:latin typeface="{template.font_family}"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="{template.theme_name}"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>
'''


def _core_properties_xml(deck_title: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>{_xml_text(deck_title)}</dc:title>
  <dc:creator>KW Studio</dc:creator>
</cp:coreProperties>
'''


def _app_properties_xml(slide_count: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>KW Studio</Application>
  <Slides>{slide_count}</Slides>
</Properties>
'''


def _xml_text(value: str) -> str:
    return escape(value, quote=False)
