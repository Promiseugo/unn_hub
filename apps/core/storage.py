"""
apps/core/storage.py

Custom Cloudinary storage that routes files to the correct Cloudinary
resource_type ('image' vs 'video') based on file extension.

Using this as the default storage means no model/migration changes are needed:
image fields receive 'image' resource_type and video fields receive 'video'.
"""
from cloudinary_storage.storage import MediaCloudinaryStorage

VIDEO_EXTENSIONS = {'mp4', 'mov', 'webm', 'avi', 'mkv', 'm4v'}


class SmartCloudinaryStorage(MediaCloudinaryStorage):
    def _get_resource_type(self, name):
        ext = name.rsplit('.', 1)[-1].lower() if '.' in str(name) else ''
        return 'video' if ext in VIDEO_EXTENSIONS else 'image'
