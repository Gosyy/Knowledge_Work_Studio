from __future__ import annotations

import io
import zipfile

from backend.app.services.slides_service.outline import SlideOutlineItem


def generate_pptx_from_outline(outline: tuple[SlideOutlineItem, ...]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as pptx_zip:
        pptx_zip.writestr("[Content_Types].xml", "<Types></Types>")
        for index, item in enumerate(outline, start=1):
            body = "\n".join((item.title, *[f"- {bullet}" for bullet in item.bullets]))
            pptx_zip.writestr(f"ppt/slides/slide{index}.txt", body)
    return buffer.getvalue()
