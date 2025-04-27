from django.core.exceptions import ValidationError
from django.conf import settings

class FileUploadValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.FILES:
            for file in request.FILES.values():
                if file.size > settings.MAX_UPLOAD_SIZE:
                    raise ValidationError(f'File size exceeds {settings.MAX_UPLOAD_SIZE} bytes')
                if file.content_type not in settings.ALLOWED_MIME_TYPES:
                    raise ValidationError(f'File type {file.content_type} not allowed')
        return self.get_response(request) 