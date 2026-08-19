"""
Artwork validation tests — comprehensive coverage of all risky cases.

Tests are grouped by concern:
  - File format detection (actual bytes, not MIME type)
  - Aspect ratio per artwork kind
  - Size limits (200 KB ceiling)
  - Corruption detection
  - Tolerance boundary cases
  - Helper function contract (detected_extension, detected_content_type)

All tests are pure unit tests that call validate_artwork() directly —
no database or HTTP required.
"""
from __future__ import annotations

import io
import os
import struct

import pytest
from PIL import Image

from app.core.image_validator import (
    ImageValidationError,
    detected_content_type,
    detected_extension,
    validate_artwork,
)


# ─────────────────────────────────────────────────────────────────────────────
# Image factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_image(width: int, height: int, fmt: str = "JPEG") -> bytes:
    """Create a valid, small in-memory image of the given dimensions."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_oversized_image(width: int, height: int, target_kb: int = 300) -> bytes:
    """
    Create a PNG image whose compressed size exceeds 200 KB.

    Uses random pixel data so the PNG compressor cannot achieve good ratios.
    Falls back gracefully: if the image happens to be small, the caller should
    use pytest.skip().
    """
    buf = io.BytesIO()
    img = Image.frombytes("RGB", (width, height), os.urandom(width * height * 3))
    img.save(buf, format="PNG", compress_level=0)
    return buf.getvalue()


def _corrupt_jpeg_data() -> bytes:
    """Return plausible-looking but corrupt JPEG bytes."""
    # Start with a valid JPEG magic and then garbage
    return b"\xff\xd8\xff\xe0" + os.urandom(500)


def _truncated_png() -> bytes:
    """Return a PNG file that is cut off mid-stream."""
    data = make_image(640, 360, "PNG")
    return data[:100]  # definitely too short to be valid


# ─────────────────────────────────────────────────────────────────────────────
# Poster (2:3, max 200 KB)
# ─────────────────────────────────────────────────────────────────────────────

class TestPoster:
    def test_valid_poster(self):
        data = make_image(600, 900)
        w, h = validate_artwork(data, "poster", "image/jpeg")
        assert w == 600 and h == 900

    def test_valid_poster_small(self):
        """Any 2:3 image passes — size below target is fine."""
        data = make_image(200, 300)
        w, h = validate_artwork(data, "poster", "image/jpeg")
        assert w == 200 and h == 300

    def test_poster_wrong_ratio_square(self):
        """1:1 aspect ratio is not 2:3."""
        data = make_image(600, 600)
        with pytest.raises(ImageValidationError, match="2:3"):
            validate_artwork(data, "poster", "image/jpeg")

    def test_poster_wrong_ratio_landscape(self):
        """16:9 landscape should fail for poster."""
        data = make_image(1280, 720)
        with pytest.raises(ImageValidationError, match="2:3"):
            validate_artwork(data, "poster", "image/jpeg")

    def test_poster_wrong_ratio_error_contains_dimensions(self):
        """Error message must include the actual image dimensions."""
        data = make_image(1024, 1024)
        with pytest.raises(ImageValidationError, match="1024×1024"):
            validate_artwork(data, "poster", "image/jpeg")

    def test_poster_error_mentions_target_dimensions(self):
        """Error must mention the target 600×900."""
        data = make_image(1024, 1024)
        with pytest.raises(ImageValidationError, match="600×900"):
            validate_artwork(data, "poster", "image/jpeg")

    def test_poster_too_large(self):
        """Image > 200 KB is rejected before opening with Pillow."""
        data = make_oversized_image(600, 900)
        if len(data) <= 200 * 1024:
            pytest.skip("Could not produce an oversized image in this environment")
        with pytest.raises(ImageValidationError, match="200 KB"):
            validate_artwork(data, "poster", "image/png")

    def test_poster_within_tolerance(self):
        """599×900 (ratio ≈ 2:3.01) is within 5% tolerance."""
        data = make_image(599, 900)
        validate_artwork(data, "poster", "image/jpeg")  # must not raise

    def test_poster_outside_tolerance(self):
        """500×900 (5:9) is >5% off 2:3."""
        data = make_image(500, 900)
        with pytest.raises(ImageValidationError):
            validate_artwork(data, "poster", "image/jpeg")

    def test_poster_png_also_valid(self):
        """PNG format is accepted for posters."""
        data = make_image(600, 900, "PNG")
        validate_artwork(data, "poster", "image/png")

    def test_poster_webp_also_valid(self):
        """WebP format is accepted for posters."""
        data = make_image(600, 900, "WEBP")
        validate_artwork(data, "poster", "image/webp")


# ─────────────────────────────────────────────────────────────────────────────
# Banner (16:9, max 200 KB)
# ─────────────────────────────────────────────────────────────────────────────

class TestBanner:
    def test_valid_banner(self):
        data = make_image(1280, 720)
        w, h = validate_artwork(data, "banner", "image/jpeg")
        assert w == 1280 and h == 720

    def test_banner_small_correct_ratio(self):
        """320×180 is 16:9 — passes aspect check regardless of size."""
        data = make_image(320, 180)
        w, h = validate_artwork(data, "banner", "image/jpeg")
        assert w == 320

    def test_banner_wrong_ratio(self):
        data = make_image(1280, 900)  # ≈ 1.42:1, not 16:9
        with pytest.raises(ImageValidationError, match="16:9"):
            validate_artwork(data, "banner", "image/jpeg")

    def test_banner_portrait_fails(self):
        """Portrait orientation fails for a landscape-ratio banner."""
        data = make_image(720, 1280)
        with pytest.raises(ImageValidationError, match="16:9"):
            validate_artwork(data, "banner", "image/jpeg")

    def test_banner_error_mentions_dimensions(self):
        data = make_image(1280, 1280)
        with pytest.raises(ImageValidationError, match="1280×1280"):
            validate_artwork(data, "banner", "image/jpeg")


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail (16:9, max 200 KB)
# ─────────────────────────────────────────────────────────────────────────────

class TestThumbnail:
    def test_valid_thumbnail(self):
        data = make_image(640, 360)
        w, h = validate_artwork(data, "thumbnail", "image/jpeg")
        assert w == 640 and h == 360

    def test_thumbnail_wrong_ratio(self):
        data = make_image(640, 480)  # 4:3, not 16:9
        with pytest.raises(ImageValidationError, match="16:9"):
            validate_artwork(data, "thumbnail", "image/jpeg")

    def test_thumbnail_mentions_target(self):
        data = make_image(640, 480)
        with pytest.raises(ImageValidationError, match="640×360"):
            validate_artwork(data, "thumbnail", "image/jpeg")


# ─────────────────────────────────────────────────────────────────────────────
# Format detection — must use bytes, NOT the HTTP Content-Type header
# ─────────────────────────────────────────────────────────────────────────────

class TestFileTypeDetection:
    def test_jpeg_bytes_accepted_regardless_of_content_type_header(self):
        """Valid JPEG bytes pass even if the HTTP header is wrong."""
        data = make_image(640, 360, "JPEG")
        # Pass a deliberately wrong content-type — should be ignored
        validate_artwork(data, "thumbnail", "application/octet-stream")

    def test_png_bytes_accepted_regardless_of_content_type_header(self):
        """Valid PNG bytes pass even if the HTTP header claims JPEG."""
        data = make_image(640, 360, "PNG")
        validate_artwork(data, "thumbnail", "image/jpeg")

    def test_random_bytes_rejected(self):
        """Random bytes that don't form a valid image are rejected."""
        with pytest.raises(ImageValidationError, match="could not be read"):
            validate_artwork(os.urandom(1024), "thumbnail", "image/jpeg")

    def test_text_file_rejected(self):
        """A plain text file is not an image."""
        with pytest.raises(ImageValidationError):
            validate_artwork(b"Hello, World! This is definitely not an image.", "thumbnail", "image/jpeg")

    def test_corrupt_jpeg_magic_rejected(self):
        """Bytes with JPEG magic bytes but corrupt body are rejected."""
        with pytest.raises(ImageValidationError):
            validate_artwork(_corrupt_jpeg_data(), "thumbnail", "image/jpeg")

    def test_truncated_png_rejected(self):
        """A truncated PNG (header only, no pixel data) is rejected."""
        with pytest.raises(ImageValidationError):
            validate_artwork(_truncated_png(), "thumbnail", "image/jpeg")

    def test_gif_not_accepted(self):
        """GIF format is not allowed (not in JPEG/PNG/WebP)."""
        img = Image.new("RGB", (640, 360), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="GIF")
        gif_data = buf.getvalue()
        with pytest.raises(ImageValidationError, match="GIF"):
            validate_artwork(gif_data, "thumbnail", "image/gif")

    def test_bmp_not_accepted(self):
        """BMP format is not allowed."""
        img = Image.new("RGB", (640, 360))
        buf = io.BytesIO()
        img.save(buf, format="BMP")
        bmp_data = buf.getvalue()
        with pytest.raises(ImageValidationError):
            validate_artwork(bmp_data, "thumbnail", "image/bmp")

    def test_html_file_disguised_as_image_rejected(self):
        """An HTML file with an image MIME type is rejected."""
        fake = b"<!DOCTYPE html><html><body>Hello</body></html>"
        with pytest.raises(ImageValidationError):
            validate_artwork(fake, "poster", "image/jpeg")

    def test_empty_bytes_rejected(self):
        """Empty upload is rejected."""
        with pytest.raises(ImageValidationError):
            validate_artwork(b"", "thumbnail", "image/jpeg")


# ─────────────────────────────────────────────────────────────────────────────
# Invalid artwork kind
# ─────────────────────────────────────────────────────────────────────────────

class TestInvalidKind:
    def test_unknown_kind(self):
        data = make_image(640, 360)
        with pytest.raises(ImageValidationError, match="Unknown artwork kind"):
            validate_artwork(data, "hero", "image/jpeg")

    def test_empty_kind(self):
        data = make_image(640, 360)
        with pytest.raises(ImageValidationError, match="Unknown artwork kind"):
            validate_artwork(data, "", "image/jpeg")


# ─────────────────────────────────────────────────────────────────────────────
# detected_extension() helper
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectedExtension:
    def test_jpeg_returns_jpg(self):
        data = make_image(640, 360, "JPEG")
        assert detected_extension(data) == "jpg"

    def test_png_returns_png(self):
        data = make_image(640, 360, "PNG")
        assert detected_extension(data) == "png"

    def test_webp_returns_webp(self):
        data = make_image(640, 360, "WEBP")
        assert detected_extension(data) == "webp"

    def test_garbage_returns_bin(self):
        assert detected_extension(b"not an image") == "bin"

    def test_empty_returns_bin(self):
        assert detected_extension(b"") == "bin"


# ─────────────────────────────────────────────────────────────────────────────
# detected_content_type() helper
# ─────────────────────────────────────────────────────────────────────────────

class TestDetectedContentType:
    def test_jpeg_detected(self):
        data = make_image(640, 360, "JPEG")
        assert detected_content_type(data) == "image/jpeg"

    def test_png_detected(self):
        data = make_image(640, 360, "PNG")
        assert detected_content_type(data) == "image/png"

    def test_webp_detected(self):
        data = make_image(640, 360, "WEBP")
        assert detected_content_type(data) == "image/webp"

    def test_garbage_returns_octet_stream(self):
        assert detected_content_type(b"garbage") == "application/octet-stream"

    def test_content_type_not_trusting_http_header(self):
        """validate_artwork detects JPEG even though we pass wrong MIME type."""
        jpeg_data = make_image(640, 360, "JPEG")
        ct = detected_content_type(jpeg_data)
        assert ct == "image/jpeg"
        # This is what validate_artwork does internally — ignores caller's MIME hint


# ─────────────────────────────────────────────────────────────────────────────
# Size limit edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestSizeLimits:
    def test_size_check_happens_before_pillow_open(self):
        """
        The size check runs before Pillow opens the file.
        A huge block of garbage should be rejected for being oversized, not for
        being invalid (since the size check fires first).
        """
        big_garbage = os.urandom(201 * 1024)  # 201 KB of noise
        with pytest.raises(ImageValidationError, match="200 KB"):
            validate_artwork(big_garbage, "thumbnail", "image/jpeg")

    def test_error_message_includes_actual_size(self):
        """The error message should tell the editor how big the file was."""
        data = make_oversized_image(640, 360)
        if len(data) <= 200 * 1024:
            pytest.skip("Could not produce oversized image")
        with pytest.raises(ImageValidationError) as exc_info:
            validate_artwork(data, "thumbnail", "image/png")
        # Should contain the size in KB
        assert "KB" in str(exc_info.value)
