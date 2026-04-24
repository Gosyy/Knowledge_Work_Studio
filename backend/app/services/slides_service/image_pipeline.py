from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import struct
import zlib
from uuid import uuid4

from backend.app.domain import StoredFile
from backend.app.repositories.interfaces import StoredFileRepository
from backend.app.repositories.storage import FileStorage
from backend.app.services.slides_service.media import ImageFitMode, SlideMediaAsset


class VisualIntent(str, Enum):
    NONE = "none"
    COVER_ILLUSTRATION = "cover_illustration"
    HERO_IMAGE = "hero_image"
    COMPARISON_VISUAL = "comparison_visual"
    PROCESS_VISUAL = "process_visual"
    PRODUCT_MOCK = "product_mock"


@dataclass(frozen=True)
class ImageSpec:
    spec_id: str
    intent: VisualIntent
    prompt: str
    aspect_ratio: str = "16:9"
    caption: str | None = None
    source_label: str | None = None
    required: bool = True


class SlideImageProvider:
    def generate(self, spec: ImageSpec) -> SlideMediaAsset:
        raise NotImplementedError


class DeterministicPatternImageProvider(SlideImageProvider):
    """Local dependency-free illustration generator for offline intranet use."""

    def generate(self, spec: ImageSpec) -> SlideMediaAsset:
        width_px, height_px = _dimensions_for_ratio(spec.aspect_ratio)
        data = _build_png(spec.prompt, width_px, height_px)
        return SlideMediaAsset(
            media_id=f"media_{spec.spec_id}",
            filename=f"{spec.spec_id}.png",
            content_type="image/png",
            data=data,
            width_px=width_px,
            height_px=height_px,
            fit_mode=ImageFitMode.CONTAIN,
            alt_text=spec.caption or spec.prompt[:120],
            caption=spec.caption,
            source_label=spec.source_label,
        )


@dataclass(frozen=True)
class RegisteredSlideMedia:
    asset: SlideMediaAsset
    stored_file: StoredFile


@dataclass
class SlideImageRegistry:
    storage: FileStorage
    stored_files: StoredFileRepository

    def register_generated_asset(
        self,
        *,
        session_id: str,
        task_id: str,
        owner_user_id: str,
        spec: ImageSpec,
        asset: SlideMediaAsset,
    ) -> RegisteredSlideMedia:
        extension = asset.extension()
        stored_file_id = f"sfimg_{uuid4().hex}"
        storage_key = f"slides/generated_media/{session_id}/{task_id}/{asset.media_id}.{extension}"
        storage_uri = self.storage.save_bytes(
            storage_key=storage_key,
            content=asset.data,
            content_type=asset.content_type,
        )
        checksum_sha256 = hashlib.sha256(asset.data).hexdigest()
        stored_file = self.stored_files.create(
            StoredFile(
                id=stored_file_id,
                session_id=session_id,
                task_id=task_id,
                kind="generated_slide_media",
                file_type=extension,
                mime_type=asset.content_type,
                title=spec.caption or spec.prompt[:80],
                original_filename=asset.filename,
                storage_backend=self.storage.backend_name,
                storage_key=storage_key,
                storage_uri=storage_uri,
                checksum_sha256=checksum_sha256,
                size_bytes=len(asset.data),
                owner_user_id=owner_user_id,
                is_remote=self.storage.backend_name != "local",
            )
        )
        registered_asset = replace(
            asset,
            stored_file_id=stored_file.id,
            storage_uri=stored_file.storage_uri,
            caption=spec.caption or asset.caption,
            source_label=spec.source_label or asset.source_label,
        )
        return RegisteredSlideMedia(asset=registered_asset, stored_file=stored_file)


def _dimensions_for_ratio(ratio: str) -> tuple[int, int]:
    normalized = (ratio or "16:9").strip()
    if normalized == "16:9":
        return 1280, 720
    if normalized == "4:3":
        return 1200, 900
    return 1280, 720


def _build_png(seed_text: str, width: int, height: int) -> bytes:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    bg = (240 + digest[0] % 16, 244 + digest[1] % 8, 248 + digest[2] % 6)
    accent_a = (32 + digest[3] % 192, 64 + digest[4] % 128, 96 + digest[5] % 128)
    accent_b = (64 + digest[6] % 160, 96 + digest[7] % 120, 128 + digest[8] % 100)
    footer = (16 + digest[9] % 64, 24 + digest[10] % 64, 40 + digest[11] % 64)

    rows = bytearray()
    band_height = max(1, height // 5)
    footer_height = max(8, height // 8)
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if y < band_height:
                color = accent_a
            elif y < band_height * 2:
                color = accent_b
            elif y >= height - footer_height:
                color = footer
            else:
                stripe = ((x // max(1, width // 12)) + (y // max(1, height // 12))) % 2
                color = bg if stripe == 0 else (min(255, bg[0] + 6), min(255, bg[1] + 6), min(255, bg[2] + 6))
            rows.extend(color)

    compressed = zlib.compress(bytes(rows), level=9)
    return b"".join([
        b"\x89PNG\r\n\x1a\n",
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        _png_chunk(b"IDAT", compressed),
        _png_chunk(b"IEND", b""),
    ])

def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc
