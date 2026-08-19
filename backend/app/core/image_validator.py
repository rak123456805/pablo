"""
Image validation: file type, aspect ratio, dimensions, and size.

Design principles:
- Never trust the HTTP Content-Type header or filename extension alone.
  Always use Pillow to detect the actual image format from bytes.
- Produce human-readable error messages suitable for a non-technical editor.
- Raise ImageValidationError with a single, clear message; caller maps to HTTP 422.
"""
from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from app.reference import ARTWORK_KINDS, ARTWORK_SPECS, artwork_aspect_ratio, artwork_max_bytes, artwork_target_px

# Only these Pillow format strings are permitted
_ALLOWED_PIL_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP"})

# Human-readable label for each kind
_KIND_LABEL: dict[str, str] = {
    "poster": "Poster",
    "banner": "Banner",
    "thumbnail": "Thumbnail",
}


class ImageValidationError(ValueError):
    """Raised when an uploaded image fails validation."""


def _aspect_ok(width: int, height: int, w_parts: int, h_parts: int, tolerance: float = 0.05) -> bool:
    """Check if width/height ratio matches w_parts/h_parts within tolerance."""
    expected = w_parts / h_parts
    actual = width / height
    return abs(actual - expected) / expected <= tolerance


def _detect_image(data: bytes, kind: str) -> Image.Image:
    """
    Open image from raw bytes using Pillow.

    Verifies the image is not corrupted, then returns a fresh Image object.
    Raises ImageValidationError with an editor-friendly message on failure.
    """
    label = _KIND_LABEL.get(kind, kind.capitalize())
    try:
        # Verify that the file is a valid image (detects corruption)
        img = Image.open(io.BytesIO(data))
        img.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageValidationError(
            f"The uploaded file could not be read as an image. "
            f"Please upload a valid JPEG, PNG, or WebP file for the {label.lower()}. "
            f"(Technical detail: {exc})"
        ) from exc

    # Re-open: verify() closes the file pointer and renders the object unusable
    img = Image.open(io.BytesIO(data))

    # Check allowed format
    fmt = (img.format or "").upper()
    if fmt not in _ALLOWED_PIL_FORMATS:
        readable = ", ".join(sorted(_ALLOWED_PIL_FORMATS))
        raise ImageValidationError(
            f"The uploaded file is a {fmt or 'unknown'} image. "
            f"{label}s must be one of: {readable}. "
            "Please convert the file and try again."
        )

    return img


def detected_extension(data: bytes) -> str:
    """
    Return the file extension ('jpg', 'png', 'webp') detected from image bytes.
    Falls back to 'bin' if format cannot be determined.
    Does NOT raise — callers handle errors via validate_artwork.
    """
    try:
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").upper()
        return {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(fmt, "bin")
    except Exception:
        return "bin"


def detected_content_type(data: bytes) -> str:
    """
    Return the MIME content type detected from image bytes.
    Falls back to 'application/octet-stream' if format cannot be determined.
    """
    try:
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").upper()
        return {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
        }.get(fmt, "application/octet-stream")
    except Exception:
        return "application/octet-stream"


def validate_artwork(data: bytes, kind: str, content_type: str) -> tuple[int, int]:
    """
    Validate image bytes against the spec for `kind`.

    Checks (in order):
      1. File size ≤ max_kb
      2. Actual image format (not HTTP Content-Type)
      3. Aspect ratio within 5% tolerance
      4. Not corrupted

    Returns (width_px, height_px) on success.
    Raises ImageValidationError with an editor-friendly message on failure.

    Note: `content_type` is accepted for API compatibility but is NOT used for
    validation — Pillow detects the actual format from the bytes.
    """
    if kind not in ARTWORK_KINDS:
        raise ImageValidationError(
            f"Unknown artwork kind '{kind}'. Allowed: {sorted(ARTWORK_KINDS)}."
        )

    label = _KIND_LABEL.get(kind, kind.capitalize())
    spec = ARTWORK_SPECS[kind]
    target_w, target_h = artwork_target_px(kind)
    aspect_str = spec["aspect"]
    w_parts, h_parts = artwork_aspect_ratio(kind)

    # ── 1. Size check ────────────────────────────────────────────────────────
    max_bytes = artwork_max_bytes(kind)
    size = len(data)
    if size > max_bytes:
        kb_actual = size / 1024
        kb_max = max_bytes / 1024
        raise ImageValidationError(
            f"The {label.lower()} image is {kb_actual:.0f} KB, but the maximum allowed is "
            f"{kb_max:.0f} KB. Please compress the image and try again."
        )

    # ── 2. Format + corruption check (uses Pillow, ignores HTTP content_type) ─
    img = _detect_image(data, kind)
    width, height = img.size

    # ── 3. Aspect ratio check ─────────────────────────────────────────────────
    if not _aspect_ok(width, height, w_parts, h_parts):
        raise ImageValidationError(
            f"{label} is {width}×{height}, but {label.lower()}s must use a {aspect_str} "
            f"{'portrait' if h_parts > w_parts else 'landscape'} ratio. "
            f"Please upload an image close to {target_w}×{target_h}."
        )

    return width, height
