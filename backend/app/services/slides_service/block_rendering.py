from __future__ import annotations

from html import escape

from backend.app.services.slides_service.blocks import (
    BulletBlock,
    BusinessMetricBlock,
    ChartBlock,
    ComparisonBlock,
    SlideBlock,
    TableBlock,
    TextBlock,
    TimelineBlock,
)
from backend.app.services.slides_service.layouts import ShapeBox, SlideLayoutSpec, SlideTemplate


def render_structured_blocks_xml(
    *,
    blocks: tuple[SlideBlock, ...],
    layout: SlideLayoutSpec,
    template: SlideTemplate,
    slide_index: int,
) -> str:
    """Render typed M13 slide blocks as real OOXML shapes, not as plain bullet fallbacks."""
    if not blocks:
        return ""
    body_boxes = layout.body_boxes or (ShapeBox(685800, 1371600, 7772400, 4572000),)

    comparison = next((block for block in blocks if isinstance(block, ComparisonBlock)), None)
    if comparison is not None:
        return _comparison_block_xml(
            block=comparison,
            boxes=body_boxes,
            template=template,
            slide_index=slide_index,
            shape_id_base=slide_index * 1000 + 100,
        )

    timeline = next((block for block in blocks if isinstance(block, TimelineBlock)), None)
    if timeline is not None:
        return _timeline_block_xml(
            block=timeline,
            box=body_boxes[0],
            template=template,
            slide_index=slide_index,
            shape_id_base=slide_index * 1000 + 200,
        )

    has_data_blocks = any(isinstance(block, (BusinessMetricBlock, TableBlock, ChartBlock)) for block in blocks)
    if has_data_blocks:
        return _data_blocks_xml(
            blocks=blocks,
            box=body_boxes[0],
            template=template,
            slide_index=slide_index,
            shape_id_base=slide_index * 1000 + 300,
        )

    return _generic_blocks_xml(
        blocks=blocks,
        boxes=body_boxes,
        template=template,
        slide_index=slide_index,
        shape_id_base=slide_index * 1000 + 400,
    )


def _generic_blocks_xml(
    *,
    blocks: tuple[SlideBlock, ...],
    boxes: tuple[ShapeBox, ...],
    template: SlideTemplate,
    slide_index: int,
    shape_id_base: int,
) -> str:
    rendered: list[str] = []
    for offset, block in enumerate(blocks, start=1):
        box = boxes[min(offset - 1, len(boxes) - 1)]
        if isinstance(block, TextBlock):
            paragraphs = (block.caption, block.text) if block.caption else (block.text,)
            rendered.append(
                _text_box_xml(
                    shape_id=shape_id_base + offset,
                    name=f"text_block {slide_index}-{offset}",
                    box=box,
                    paragraphs=tuple(part for part in paragraphs if part),
                    font_size=1800,
                    color=template.body_color,
                    font_family=template.font_family,
                    alignment="ctr",
                )
            )
        elif isinstance(block, BulletBlock):
            rendered.append(
                _bullet_block_xml(
                    block=block,
                    box=box,
                    template=template,
                    shape_id=shape_id_base + offset,
                    name=f"bullet_block {slide_index}-{offset}",
                )
            )
        elif isinstance(block, TableBlock):
            rendered.append(_table_block_xml(block=block, box=box, template=template, shape_id_base=shape_id_base + offset * 20))
        elif isinstance(block, ChartBlock):
            rendered.append(_chart_block_xml(block=block, box=box, template=template, shape_id_base=shape_id_base + offset * 20))
        elif isinstance(block, BusinessMetricBlock):
            rendered.append(_business_metric_block_xml(block=block, box=box, template=template, shape_id_base=shape_id_base + offset * 20))
        elif isinstance(block, TimelineBlock):
            rendered.append(
                _timeline_block_xml(
                    block=block,
                    box=box,
                    template=template,
                    slide_index=slide_index,
                    shape_id_base=shape_id_base + offset * 20,
                )
            )
        elif isinstance(block, ComparisonBlock):
            rendered.append(
                _comparison_block_xml(
                    block=block,
                    boxes=boxes,
                    template=template,
                    slide_index=slide_index,
                    shape_id_base=shape_id_base + offset * 20,
                )
            )
    return "\n".join(part for part in rendered if part)


def _data_blocks_xml(
    *,
    blocks: tuple[SlideBlock, ...],
    box: ShapeBox,
    template: SlideTemplate,
    slide_index: int,
    shape_id_base: int,
) -> str:
    metric_block = next((block for block in blocks if isinstance(block, BusinessMetricBlock)), None)
    table_block = next((block for block in blocks if isinstance(block, TableBlock)), None)
    chart_block = next((block for block in blocks if isinstance(block, ChartBlock)), None)

    rendered: list[str] = []
    cursor_y = box.y
    remaining_cy = box.cy
    if metric_block is not None:
        metric_cy = min(914400, max(640080, box.cy // 4))
        metric_box = ShapeBox(box.x, cursor_y, box.cx, metric_cy)
        rendered.append(_business_metric_block_xml(block=metric_block, box=metric_box, template=template, shape_id_base=shape_id_base + 10))
        cursor_y += metric_cy + 114300
        remaining_cy = max(1, box.y + box.cy - cursor_y)

    lower_box = ShapeBox(box.x, cursor_y, box.cx, remaining_cy)
    if table_block is not None and chart_block is not None:
        gap = 137160
        left_cx = (lower_box.cx - gap) // 2
        right_cx = lower_box.cx - left_cx - gap
        table_box = ShapeBox(lower_box.x, lower_box.y, left_cx, lower_box.cy)
        chart_box = ShapeBox(lower_box.x + left_cx + gap, lower_box.y, right_cx, lower_box.cy)
        rendered.append(_table_block_xml(block=table_block, box=table_box, template=template, shape_id_base=shape_id_base + 100))
        rendered.append(_chart_block_xml(block=chart_block, box=chart_box, template=template, shape_id_base=shape_id_base + 200))
    elif table_block is not None:
        rendered.append(_table_block_xml(block=table_block, box=lower_box, template=template, shape_id_base=shape_id_base + 100))
    elif chart_block is not None:
        rendered.append(_chart_block_xml(block=chart_block, box=lower_box, template=template, shape_id_base=shape_id_base + 200))
    else:
        remaining = tuple(block for block in blocks if not isinstance(block, BusinessMetricBlock))
        rendered.append(
            _generic_blocks_xml(
                blocks=remaining,
                boxes=(lower_box,),
                template=template,
                slide_index=slide_index,
                shape_id_base=shape_id_base + 300,
            )
        )
    return "\n".join(part for part in rendered if part)


def _business_metric_block_xml(*, block: BusinessMetricBlock, box: ShapeBox, template: SlideTemplate, shape_id_base: int) -> str:
    if not block.metrics:
        raise ValueError(f"Business metric block '{block.block_id}' has no metrics.")
    rendered: list[str] = []
    metrics = block.metrics[:4]
    gap = 91440
    card_cx = max(1, (box.cx - gap * (len(metrics) - 1)) // len(metrics))
    caption_offset = 0
    if block.caption:
        caption_cy = min(228600, max(1, box.cy // 3))
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base,
                name=f"business_metric_block caption {block.block_id}",
                box=ShapeBox(box.x, box.y, box.cx, caption_cy),
                paragraphs=(block.caption,),
                font_size=1200,
                color=template.body_color,
                font_family=template.font_family,
                alignment="l",
                bold=True,
            )
        )
        caption_offset = caption_cy + 45720
    card_y = box.y + caption_offset
    card_cy = max(1, box.cy - caption_offset)
    for offset, metric in enumerate(metrics, start=1):
        card_box = ShapeBox(box.x + (offset - 1) * (card_cx + gap), card_y, card_cx, card_cy)
        paragraphs = (metric.label, metric.value) + ((metric.note,) if metric.note else ())
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base + offset,
                name=f"business_metric_block card {block.block_id}-{offset}",
                box=card_box,
                paragraphs=paragraphs,
                font_size=1150,
                color=template.body_color,
                font_family=template.font_family,
                alignment="ctr",
                fill_color="F2F6FC",
                line_color="D9E2F3",
            )
        )
    return "\n".join(rendered)


def _table_block_xml(*, block: TableBlock, box: ShapeBox, template: SlideTemplate, shape_id_base: int) -> str:
    if not block.columns:
        raise ValueError(f"Table block '{block.block_id}' has no columns.")
    for row in block.rows:
        if len(row) != len(block.columns):
            raise ValueError(f"Table block '{block.block_id}' row has {len(row)} cell(s), expected {len(block.columns)}.")

    rendered: list[str] = []
    caption_cy = 274320 if block.caption else 0
    if block.caption:
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base,
                name=f"table_block caption {block.block_id}",
                box=ShapeBox(box.x, box.y, box.cx, caption_cy),
                paragraphs=(block.caption,),
                font_size=1100,
                color=template.body_color,
                font_family=template.font_family,
                alignment="l",
                bold=True,
            )
        )
    table_y = box.y + caption_cy
    table_cy = max(1, box.cy - caption_cy)
    row_count = 1 + len(block.rows)
    row_cy = max(1, table_cy // row_count)
    col_count = len(block.columns)
    col_cx = max(1, box.cx // col_count)

    rows = (block.columns,) + block.rows
    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            cell_box = ShapeBox(
                box.x + col_index * col_cx,
                table_y + row_index * row_cy,
                col_cx if col_index < col_count - 1 else box.cx - col_cx * (col_count - 1),
                row_cy,
            )
            is_header = row_index == 0
            rendered.append(
                _text_box_xml(
                    shape_id=shape_id_base + 1 + row_index * col_count + col_index,
                    name=f"table_block cell {block.block_id}-{row_index}-{col_index}",
                    box=cell_box,
                    paragraphs=(_clip_text(cell, 42),),
                    font_size=900 if len(block.rows) > 3 else 1050,
                    color=template.title_color if is_header else template.body_color,
                    font_family=template.font_family,
                    alignment="ctr" if is_header else "l",
                    fill_color="E9EEF7" if is_header else "FFFFFF",
                    line_color="D9E2F3",
                    bold=is_header,
                )
            )
    return "\n".join(rendered)


def _chart_block_xml(*, block: ChartBlock, box: ShapeBox, template: SlideTemplate, shape_id_base: int) -> str:
    if len(block.categories) != len(block.values):
        raise ValueError(f"Chart block '{block.block_id}' has {len(block.categories)} categories but {len(block.values)} values.")
    if not block.values:
        raise ValueError(f"Chart block '{block.block_id}' has no values.")

    rendered: list[str] = []
    title_cy = 342900
    rendered.append(
        _text_box_xml(
            shape_id=shape_id_base,
            name=f"chart_block title {block.block_id}",
            box=ShapeBox(box.x, box.y, box.cx, title_cy),
            paragraphs=(block.title,),
            font_size=1100,
            color=template.body_color,
            font_family=template.font_family,
            alignment="l",
            bold=True,
        )
    )
    plot_box = ShapeBox(box.x, box.y + title_cy, box.cx, max(1, box.cy - title_cy))
    max_value = max(abs(value) for value in block.values) or 1.0
    bar_count = len(block.values)
    row_cy = max(1, plot_box.cy // bar_count)
    label_cx = min(plot_box.cx // 3, 914400)
    value_cx = min(457200, plot_box.cx // 6)
    bar_area_cx = max(1, plot_box.cx - label_cx - value_cx - 91440)

    for offset, (category, value) in enumerate(zip(block.categories, block.values, strict=True), start=1):
        row_y = plot_box.y + (offset - 1) * row_cy
        label_box = ShapeBox(plot_box.x, row_y, label_cx, row_cy)
        bar_cx = max(1, round(bar_area_cx * (abs(value) / max_value)))
        bar_cy = max(45720, row_cy // 3)
        bar_y = row_y + max(0, (row_cy - bar_cy) // 2)
        bar_box = ShapeBox(plot_box.x + label_cx + 45720, bar_y, bar_cx, bar_cy)
        value_box = ShapeBox(plot_box.x + label_cx + bar_area_cx + 91440, row_y, value_cx, row_cy)
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base + offset * 3 - 2,
                name=f"chart_block category {block.block_id}-{offset}",
                box=label_box,
                paragraphs=(_clip_text(category, 24),),
                font_size=850,
                color=template.body_color,
                font_family=template.font_family,
                alignment="l",
            )
        )
        rendered.append(
            _shape_xml(
                shape_id=shape_id_base + offset * 3 - 1,
                name=f"chart_block bar {block.block_id}-{offset}",
                box=bar_box,
                fill_color=template.accent_color,
                line_color=template.accent_color,
            )
        )
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base + offset * 3,
                name=f"chart_block value {block.block_id}-{offset}",
                box=value_box,
                paragraphs=(f"{value:g}{(' ' + block.unit) if block.unit else ''}",),
                font_size=850,
                color=template.body_color,
                font_family=template.font_family,
                alignment="r",
            )
        )
    return "\n".join(rendered)


def _comparison_block_xml(
    *,
    block: ComparisonBlock,
    boxes: tuple[ShapeBox, ...],
    template: SlideTemplate,
    slide_index: int,
    shape_id_base: int,
) -> str:
    if not boxes:
        raise ValueError(f"Comparison block '{block.block_id}' has no layout boxes.")
    if len(boxes) >= 2:
        left_box, right_box = boxes[0], boxes[1]
    else:
        gap = 137160
        left_cx = (boxes[0].cx - gap) // 2
        right_cx = boxes[0].cx - left_cx - gap
        left_box = ShapeBox(boxes[0].x, boxes[0].y, left_cx, boxes[0].cy)
        right_box = ShapeBox(boxes[0].x + left_cx + gap, boxes[0].y, right_cx, boxes[0].cy)
    return "\n".join(
        (
            _comparison_column_xml(
                title=block.left_title,
                items=block.left_items,
                box=left_box,
                template=template,
                shape_id=shape_id_base + 1,
                name=f"comparison_block left {block.block_id}-{slide_index}",
            ),
            _comparison_column_xml(
                title=block.right_title,
                items=block.right_items,
                box=right_box,
                template=template,
                shape_id=shape_id_base + 2,
                name=f"comparison_block right {block.block_id}-{slide_index}",
            ),
        )
    )


def _comparison_column_xml(*, title: str, items: tuple[str, ...], box: ShapeBox, template: SlideTemplate, shape_id: int, name: str) -> str:
    paragraphs = (title,) + tuple(items or ("No comparison item provided",))
    return _text_box_xml(
        shape_id=shape_id,
        name=name,
        box=box,
        paragraphs=paragraphs,
        font_size=1200,
        color=template.body_color,
        font_family=template.font_family,
        alignment="l",
        fill_color="F7F9FC",
        line_color="D9E2F3",
        bold=True,
    )


def _timeline_block_xml(
    *,
    block: TimelineBlock,
    box: ShapeBox,
    template: SlideTemplate,
    slide_index: int,
    shape_id_base: int,
) -> str:
    if not block.items:
        raise ValueError(f"Timeline block '{block.block_id}' has no items.")
    items = block.items[:5]
    rendered: list[str] = []
    if block.caption:
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base,
                name=f"timeline_block caption {block.block_id}",
                box=ShapeBox(box.x, box.y, box.cx, 342900),
                paragraphs=(block.caption,),
                font_size=1100,
                color=template.body_color,
                font_family=template.font_family,
                alignment="l",
                bold=True,
            )
        )
    timeline_y = box.y + max(685800, box.cy // 3)
    rendered.append(
        _shape_xml(
            shape_id=shape_id_base + 1,
            name=f"timeline_block line {block.block_id}-{slide_index}",
            box=ShapeBox(box.x + 228600, timeline_y, max(1, box.cx - 457200), 45720),
            fill_color="D9E2F3",
            line_color="D9E2F3",
        )
    )
    slot_cx = max(1, box.cx // len(items))
    for offset, item in enumerate(items, start=1):
        slot_x = box.x + (offset - 1) * slot_cx
        marker_box = ShapeBox(slot_x + slot_cx // 2 - 91440, timeline_y - 91440, 182880, 182880)
        label_box = ShapeBox(slot_x, max(box.y, timeline_y - 640080), slot_cx, 274320)
        detail_box = ShapeBox(slot_x, timeline_y + 228600, slot_cx, max(457200, box.y + box.cy - timeline_y - 228600))
        rendered.append(
            _shape_xml(
                shape_id=shape_id_base + offset * 3,
                name=f"timeline_block marker {block.block_id}-{offset}",
                box=marker_box,
                fill_color=template.accent_color,
                line_color=template.accent_color,
                geometry="ellipse",
            )
        )
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base + offset * 3 + 1,
                name=f"timeline_block label {block.block_id}-{offset}",
                box=label_box,
                paragraphs=(item.label,),
                font_size=950,
                color=template.title_color,
                font_family=template.font_family,
                alignment="ctr",
                bold=True,
            )
        )
        rendered.append(
            _text_box_xml(
                shape_id=shape_id_base + offset * 3 + 2,
                name=f"timeline_block detail {block.block_id}-{offset}",
                box=detail_box,
                paragraphs=(_clip_text(item.detail, 68),),
                font_size=850,
                color=template.body_color,
                font_family=template.font_family,
                alignment="ctr",
            )
        )
    return "\n".join(rendered)


def _bullet_block_xml(*, block: BulletBlock, box: ShapeBox, template: SlideTemplate, shape_id: int, name: str) -> str:
    paragraph_xml: list[str] = []
    if block.heading:
        paragraph_xml.append(
            _plain_paragraph_xml(
                text=block.heading,
                font_size=1300,
                color=template.title_color,
                font_family=template.font_family,
                alignment="l",
                bold=True,
            )
        )
    paragraph_xml.extend(
        _bullet_paragraph_xml(
            text=item,
            font_size=1500,
            color=template.body_color,
            font_family=template.font_family,
            alignment="l",
            accent_color=template.accent_color,
        )
        for item in block.bullets
    )
    if not paragraph_xml:
        paragraph_xml.append(
            _plain_paragraph_xml(
                text="No block content provided",
                font_size=1500,
                color=template.body_color,
                font_family=template.font_family,
                alignment="l",
            )
        )
    return f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{shape_id}" name="{_xml_attr(name)}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.cx}" cy="{box.cy}"/></a:xfrm></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/>
{chr(10).join(paragraph_xml)}
        </p:txBody>
      </p:sp>'''


def _text_box_xml(
    *,
    shape_id: int,
    name: str,
    box: ShapeBox,
    paragraphs: tuple[str, ...],
    font_size: int,
    color: str,
    font_family: str,
    alignment: str = "l",
    fill_color: str | None = None,
    line_color: str | None = None,
    bold: bool = False,
) -> str:
    text_paragraphs = paragraphs or ("",)
    paragraph_xml = "\n".join(
        _plain_paragraph_xml(
            text=paragraph,
            font_size=font_size,
            color=color,
            font_family=font_family,
            alignment=alignment,
            bold=bold if offset == 0 else False,
        )
        for offset, paragraph in enumerate(text_paragraphs)
    )
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill_color}"/></a:solidFill>' if fill_color else '<a:noFill/>'
    line_xml = f'<a:ln><a:solidFill><a:srgbClr val="{line_color}"/></a:solidFill></a:ln>' if line_color else '<a:ln><a:noFill/></a:ln>'
    return f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{shape_id}" name="{_xml_attr(name)}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.cx}" cy="{box.cy}"/></a:xfrm>{fill_xml}{line_xml}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/>
{paragraph_xml}
        </p:txBody>
      </p:sp>'''


def _shape_xml(*, shape_id: int, name: str, box: ShapeBox, fill_color: str, line_color: str, geometry: str = "rect") -> str:
    return f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{shape_id}" name="{_xml_attr(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{box.x}" y="{box.y}"/><a:ext cx="{box.cx}" cy="{box.cy}"/></a:xfrm><a:solidFill><a:srgbClr val="{fill_color}"/></a:solidFill><a:ln><a:solidFill><a:srgbClr val="{line_color}"/></a:solidFill></a:ln><a:prstGeom prst="{geometry}"><a:avLst/></a:prstGeom></p:spPr>
      </p:sp>'''


def _plain_paragraph_xml(*, text: str, font_size: int, color: str, font_family: str, alignment: str, bold: bool = False) -> str:
    bold_attr = ' b="1"' if bold else ""
    return (
        '          <a:p><a:pPr algn="{alignment}"/>'
        '<a:r><a:rPr lang="en-US" sz="{font_size}"{bold_attr}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font_family}"/></a:rPr><a:t>{text}</a:t></a:r></a:p>'
    ).format(alignment=alignment, font_size=font_size, bold_attr=bold_attr, color=color, font_family=font_family, text=_xml_text(text))


def _bullet_paragraph_xml(*, text: str, font_size: int, color: str, font_family: str, alignment: str, accent_color: str) -> str:
    return (
        '          <a:p><a:pPr lvl="0" algn="{alignment}"><a:buChar char="•"/><a:defRPr sz="{font_size}"><a:solidFill><a:srgbClr val="{accent_color}"/></a:solidFill></a:defRPr></a:pPr>'
        '<a:r><a:rPr lang="en-US" sz="{font_size}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font_family}"/></a:rPr><a:t>{text}</a:t></a:r></a:p>'
    ).format(alignment=alignment, font_size=font_size, color=color, font_family=font_family, accent_color=accent_color, text=_xml_text(text))


def _clip_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def _xml_text(value: object) -> str:
    return escape(str(value), quote=False)


def _xml_attr(value: object) -> str:
    return escape(str(value), quote=True)
