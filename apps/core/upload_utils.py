"""
core/upload_utils.py

Secure file saving utilities.
Replaces user-supplied filenames with UUIDs to prevent:
  - Path traversal attacks
  - Filename-based information disclosure
  - Duplicate filename collisions
"""
import uuid
import os
import io
from django.core.files.base import ContentFile
from django.conf import settings
from .validators import sanitize_filename


def secure_video_save(model_instance, video_file, field_name='video'):
    """
    Save a video file with a UUID-based filename.
    Discards the original filename entirely — prevents all filename attacks.

    Usage in views:
        from apps.core.upload_utils import secure_video_save
        secure_video_save(listing, video_file, 'video')
        listing.save()
    """
    if not video_file:
        return

    # Get original extension (already validated upstream)
    original_name = getattr(video_file, 'name', 'upload.mp4')
    safe_name = sanitize_filename(original_name)
    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else 'mp4'

    # Generate UUID filename — impossible to guess, impossible to traverse
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    # Read content and create a new ContentFile with the safe name
    video_file.seek(0)
    content = video_file.read()
    video_file.seek(0)

    safe_file = ContentFile(content, name=new_filename)
    setattr(model_instance, field_name, safe_file)


def compressed_image_file(image_file):
    """
    Return a safely named, compressed JPEG ContentFile for user-uploaded images.
    Validation happens before this function; this handles storage hygiene and size.
    """
    from PIL import Image, ImageOps

    max_dimension = getattr(settings, 'IMAGE_UPLOAD_MAX_DIMENSION', 1600)
    quality = getattr(settings, 'IMAGE_UPLOAD_QUALITY', 82)

    image_file.seek(0)
    with Image.open(image_file) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ('RGB', 'L'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if 'A' in img.getbands():
                background.paste(img, mask=img.getchannel('A'))
            else:
                background.paste(img)
            img = background
        else:
            img = img.convert('RGB')

        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)

    original_name = getattr(image_file, 'name', 'image.jpg')
    safe_name = sanitize_filename(original_name).rsplit('.', 1)[0] or 'image'
    new_filename = f"{safe_name[:60]}_{uuid.uuid4().hex[:12]}.jpg"
    output.seek(0)
    image_file.seek(0)
    return ContentFile(output.read(), name=new_filename)
