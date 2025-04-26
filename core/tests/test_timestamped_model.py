from django.utils import timezone
from django.test import TestCase
from core.models import TestTimestampedModel

class TimestampedModelTests(TestCase):
    def test_timestamps_set_on_create(self):
        """Verify created_at and updated_at are set on creation."""
        now = timezone.now()
        instance = TestTimestampedModel.objects.create(name="Test")
        self.assertIsNotNone(instance.created_at)
        self.assertTrue(instance.created_at.tzinfo is not None)
        self.assertAlmostEqual(instance.created_at, now, delta=timezone.timedelta(seconds=1))
        self.assertAlmostEqual(instance.created_at, instance.updated_at, delta=timezone.timedelta(milliseconds=1))

    def test_updated_at_changes_on_update(self):
        """Verify updated_at changes on save() but created_at doesn't."""
        instance = TestTimestampedModel.objects.create(name="Test Update")
        created_timestamp = instance.created_at
        # Ensure some time passes
        import time; time.sleep(0.01)
        now_before_save = timezone.now()
        instance.name = "Updated Name"
        instance.save()
        # Re-fetch to ensure DB value is checked if using DB tests
        instance.refresh_from_db()

        self.assertEqual(instance.created_at, created_timestamp)  # Should not change
        self.assertNotEqual(instance.updated_at, created_timestamp)
        self.assertTrue(instance.updated_at > created_timestamp)
        self.assertTrue(instance.updated_at.tzinfo is not None)
        self.assertAlmostEqual(instance.updated_at, now_before_save, delta=timezone.timedelta(seconds=1)) 