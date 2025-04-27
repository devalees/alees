from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from core.middleware.file_validation import FileUploadValidationMiddleware

@override_settings(
    MAX_UPLOAD_SIZE=10 * 1024 * 1024,  # 10MB
    ALLOWED_MIME_TYPES=[
        'image/jpeg',
        'image/png',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
)
class FileUploadValidationMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = FileUploadValidationMiddleware(lambda r: r)
        
        # Create test files
        self.small_file = SimpleUploadedFile(
            "small.pdf", b"small content", content_type="application/pdf"
        )
        self.large_file = SimpleUploadedFile(
            "large.pdf", b"x" * (10 * 1024 * 1024 + 1),  # 10MB + 1 byte
            content_type="application/pdf"
        )
        self.allowed_image = SimpleUploadedFile(
            "test.jpg", b"fake image content", content_type="image/jpeg"
        )
        self.disallowed_file = SimpleUploadedFile(
            "test.exe", b"fake exe content", content_type="application/x-msdownload"
        )

    def test_valid_file_upload(self):
        """Test that valid file upload passes validation"""
        request = self.factory.post('/upload/', {'file': self.small_file})
        response = self.middleware(request)
        self.assertEqual(response, request)

    def test_large_file_validation(self):
        """Test that files exceeding size limit are rejected"""
        request = self.factory.post('/upload/', {'file': self.large_file})
        with self.assertRaises(ValidationError) as context:
            self.middleware(request)
        self.assertIn('File size exceeds', str(context.exception))

    def test_allowed_mime_type(self):
        """Test that allowed MIME types pass validation"""
        request = self.factory.post('/upload/', {'file': self.allowed_image})
        response = self.middleware(request)
        self.assertEqual(response, request)

    def test_disallowed_mime_type(self):
        """Test that disallowed MIME types are rejected"""
        request = self.factory.post('/upload/', {'file': self.disallowed_file})
        with self.assertRaises(ValidationError) as context:
            self.middleware(request)
        self.assertIn('File type', str(context.exception))

    def test_multiple_files_validation(self):
        """Test validation with multiple files"""
        request = self.factory.post('/upload/', {
            'file1': self.small_file,
            'file2': self.allowed_image
        })
        response = self.middleware(request)
        self.assertEqual(response, request)

    def test_multiple_files_with_invalid(self):
        """Test validation fails if any file is invalid"""
        request = self.factory.post('/upload/', {
            'file1': self.small_file,
            'file2': self.disallowed_file
        })
        with self.assertRaises(ValidationError):
            self.middleware(request)

    def test_non_file_upload_request(self):
        """Test that non-file upload requests pass through"""
        request = self.factory.post('/api/', {'data': 'test'})
        response = self.middleware(request)
        self.assertEqual(response, request)

    def test_get_request(self):
        """Test that GET requests pass through"""
        request = self.factory.get('/api/')
        response = self.middleware(request)
        self.assertEqual(response, request) 