from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImageFitMode(str, Enum):
    CONTAIN = "contain"
    COVER = "cover"
    STRETCH = "stretch"


@dataclass(frozen=True)
class SlideMediaAsset:
    media_id: str
    filename: str
    content_type: str
    data: bytes
    width_px: int
    height_px: int
    fit_mode: ImageFitMode = ImageFitMode.CONTAIN
    alt_text: str | None = None
    caption: str | None = None
    source_label: str | None = None
    stored_file_id: str | None = None
    storage_uri: str | None = None

    def extension(self) -> str:
        content_type = (self.content_type or "").lower().strip()
        filename = self.filename.rsplit(".", 1)[-1].lower() if "." in self.filename else ""
        if content_type == "image/png" or filename == "png":
            return "png"
        if content_type in {"image/jpeg", "image/jpg"} or filename in {"jpg", "jpeg"}:
            return "jpg"
        if content_type == "image/gif" or filename == "gif":
            return "gif"
        raise ValueError(
            f"Unsupported slide media content type '{self.content_type}' for asset '{self.media_id}'."
        )

    def normalized_dimensions(self) -> tuple[int, int]:
        width = max(1, int(self.width_px))
        height = max(1, int(self.height_px))
        return width, height
