from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlideOutlineItem:
    title: str
    bullets: tuple[str, ...]


def build_slides_outline(source_text: str, *, min_slides: int = 5, max_slides: int = 10) -> tuple[SlideOutlineItem, ...]:
    segments = [segment.strip() for segment in source_text.replace("\n", ". ").split(".") if segment.strip()]
    if not segments:
        segments = ["Untitled presentation"]

    outline_items: list[SlideOutlineItem] = []
    for index, segment in enumerate(segments[:max_slides], start=1):
        title = f"Slide {index}: {segment[:36]}".strip()
        outline_items.append(SlideOutlineItem(title=title, bullets=(segment,)))

    while len(outline_items) < min_slides:
        index = len(outline_items) + 1
        filler = f"Additional insight {index}"
        outline_items.append(SlideOutlineItem(title=f"Slide {index}: {filler.title()}", bullets=(filler,)))

    return tuple(outline_items[:max_slides])
