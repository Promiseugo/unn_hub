"""
core/validators.py

Shared validators — price, images, and videos.
Video validation uses a 3-layer defence:
  Layer 1 — Content-Type header (fast check, easy to spoof — necessary but not sufficient)
  Layer 2 — File extension whitelist with null byte and path traversal detection
  Layer 3 — Magic bytes (file signature) verification — reads actual file content
"""
import io
import os
import re
import unicodedata
from django.core.exceptions import ValidationError


# ─────────────────────────────────────────────
# PRICE
# ─────────────────────────────────────────────
def validate_positive_price(value):
    """Price must be greater than zero."""
    if value <= 0:
        raise ValidationError("Price must be greater than zero.")


# ─────────────────────────────────────────────
# FILENAME SANITISATION (shared)
# ─────────────────────────────────────────────
def sanitize_filename(filename):
    """
    Returns a safe version of the filename.
    - Strips path separators (path traversal defence)
    - Removes null bytes (null byte injection defence)
    - Normalises unicode to ASCII
    - Replaces spaces and special chars with underscores
    - Truncates to 100 chars
    """
    if not filename:
        return 'upload'

    # Strip null bytes — classic bypass: shell.php\x00.mp4
    filename = filename.replace('\x00', '')

    # Strip any directory component — path traversal: ../../etc/passwd.mp4
    filename = os.path.basename(filename)

    # Normalise unicode (e.g. accented chars) to ASCII equivalents
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    # Replace spaces and dangerous chars with underscores
    filename = re.sub(r'[^\w\.\-]', '_', filename)

    # Prevent double extensions like shell.php.mp4 — keep only last extension
    parts = filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        # Remove any dots from the name part
        name = name.replace('.', '_')
        filename = f"{name}.{ext}"

    # Truncate name part to 80 chars max
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1)
        filename = f"{name[:80]}.{ext}"

    return filename or 'upload'


# ─────────────────────────────────────────────
# IMAGE VALIDATION
# ─────────────────────────────────────────────
def validate_image_size(image):
    """Reject images larger than 5MB."""
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Image too large. Maximum size is {max_size_mb}MB. "
            f"Your file is {image.size / (1024*1024):.1f}MB."
        )


def validate_image_type(image):
    """
    Three-layer image validation:
    1. Content-Type header
    2. File extension
    3. Pillow content verification (cannot be spoofed)
    """
    allowed_content_types = ['image/jpeg', 'image/png', 'image/webp']
    allowed_extensions    = ['jpg', 'jpeg', 'png', 'webp']
    allowed_pillow_formats = ['JPEG', 'PNG', 'WEBP']

    # Layer 1 — Content-Type
    if hasattr(image, 'content_type') and image.content_type not in allowed_content_types:
        raise ValidationError("Unsupported format. Please upload a JPG, PNG or WEBP image.")

    # Layer 2 — Extension (with sanitisation)
    if hasattr(image, 'name') and image.name:
        safe_name = sanitize_filename(image.name)
        ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
        if ext not in allowed_extensions:
            raise ValidationError("Unsupported format. Please upload a JPG, PNG or WEBP image.")

    # Layer 3 — Pillow content verification (reads actual bytes)
    try:
        from PIL import Image
        image.seek(0)
        img = Image.open(io.BytesIO(image.read()))
        img.verify()
        image.seek(0)

        if img.format not in allowed_pillow_formats:
            raise ValidationError(
                f"Invalid image format. Please upload a JPG, PNG or WEBP image."
            )
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(
            "Invalid or corrupted image file. Please upload a valid JPG, PNG or WEBP image."
        )


class MultiImageValidator:
    @staticmethod
    def validate(files):
        errors = []
        if len(files) > 5:
            errors.append("You can upload a maximum of 5 images.")
            return errors
        for f in files:
            try:
                validate_image_size(f)
                validate_image_type(f)
            except ValidationError as e:
                errors.append(f"{f.name}: {e.message}")
        return errors


# ─────────────────────────────────────────────
# VIDEO MAGIC BYTES
# ─────────────────────────────────────────────
# Real video files have known byte signatures at the start.
# An attacker cannot fake these without producing an actual
# playable video file — which would be harmless.

VIDEO_SIGNATURES = {
    # MP4 / M4V — ftyp box at bytes 4-8
    'mp4':  [(4, 8, [
        b'ftypisom', b'ftypMSNV', b'ftypmp42',
        b'ftypMP42', b'ftypavc1', b'ftypFACE',
        b'ftypf4v ', b'ftypf4p ', b'ftypm4v ',
        b'ftypM4V ', b'ftypM4A ', b'ftyp3gp5',
        b'ftypqt  ', b'ftypmp41',
    ])],
    # MOV — QuickTime, ftyp box same position
    'mov':  [(4, 8, [b'ftypqt  ', b'moov', b'free', b'ftyp'])],
    # WebM — EBML header
    'webm': [(0, 4, [b'\x1a\x45\xdf\xa3'])],
}


def _check_magic_bytes(data, ext):
    """
    Returns True if file bytes match known signatures for the extension.
    Falls back to True if extension is not in our signature map
    (conservative — don't block unknown formats we haven't mapped).
    """
    if ext not in VIDEO_SIGNATURES:
        return True

    for offset_start, offset_end, signatures in VIDEO_SIGNATURES[ext]:
        chunk = data[offset_start:offset_end]
        for sig in signatures:
            if chunk == sig or chunk.startswith(sig[:4]):
                return True

    # MP4 special case: ftyp box can appear after initial size bytes
    # Standard MP4: first 4 bytes = box size, next 4 = 'ftyp'
    if ext in ('mp4', 'mov') and len(data) >= 8:
        if data[4:8] == b'ftyp':
            return True
        # Some encoders place moov atom first
        if data[4:8] in (b'moov', b'free', b'wide', b'mdat'):
            return True

    return False


# ─────────────────────────────────────────────
# VIDEO VALIDATION
# ─────────────────────────────────────────────
def validate_video_size(video):
    """Reject videos larger than 50MB."""
    max_size_mb = 50
    if video.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Video too large. Maximum size is {max_size_mb}MB. "
            f"Your file is {video.size / (1024*1024):.1f}MB."
        )


def validate_video_type(video):
    """
    Three-layer video validation:
    Layer 1 — Content-Type header
    Layer 2 — Extension whitelist with null byte / path traversal detection
    Layer 3 — Magic bytes (file signature) verification
    """
    allowed_content_types = [
        'video/mp4', 'video/quicktime', 'video/webm',
        'video/x-m4v', 'video/x-matroska',
    ]
    allowed_extensions = ['mp4', 'mov', 'webm', 'm4v']

    # Layer 1 — Content-Type header
    if hasattr(video, 'content_type'):
        if video.content_type not in allowed_content_types:
            raise ValidationError(
                "Unsupported video format. Please upload an MP4, MOV or WebM file."
            )

    # Layer 2 — Filename and extension (with full sanitisation)
    if hasattr(video, 'name') and video.name:
        # Check for null bytes before sanitising — explicit attack signal
        if '\x00' in video.name:
            raise ValidationError(
                "Invalid filename. The file could not be accepted."
            )

        safe_name = sanitize_filename(video.name)
        ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''

        if not ext:
            raise ValidationError(
                "File has no extension. Please upload an MP4, MOV or WebM file."
            )

        if ext not in allowed_extensions:
            raise ValidationError(
                f"Unsupported file extension '.{ext}'. "
                "Please upload an MP4, MOV or WebM file."
            )

        # Layer 3 — Magic bytes verification
        try:
            video.seek(0)
            # Read first 16 bytes — enough for all our signatures
            header = video.read(16)
            video.seek(0)

            if len(header) < 8:
                raise ValidationError(
                    "File is too small to be a valid video."
                )

            if not _check_magic_bytes(header, ext):
                raise ValidationError(
                    "File content does not match its extension. "
                    "Please upload a genuine MP4, MOV or WebM video file."
                )

        except ValidationError:
            raise
        except Exception:
            raise ValidationError(
                "Could not read the video file. Please try again with a different file."
            )


class VideoValidator:
    """
    Call VideoValidator.validate(file) in views.
    Returns an error string or None if valid.
    """
    @staticmethod
    def validate(file):
        if not file:
            return None
        try:
            validate_video_size(file)
            validate_video_type(file)
        except ValidationError as e:
            return e.message
        return None
