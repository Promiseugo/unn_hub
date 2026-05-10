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
from django.core.files.base import ContentFile
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
