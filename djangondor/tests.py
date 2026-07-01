from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TransactionTestCase

from . import bulk
from .middleware import _current_user
from .models import AuditableBaseTimestampModel, AuditableUUIDBaseTimestampModel, AuditLog


class AuditWidget(AuditableBaseTimestampModel):
    """Test-only model used to exercise `AuditLogMixin`. Not part of any migration —
    its table is created/dropped directly around this test case."""

    name = models.CharField(max_length=50)

    class Meta:
        app_label = "djangondor"


class AuditCategory(models.Model):
    """Plain (non-audited) related model, used to exercise ForeignKey tracking."""

    name = models.CharField(max_length=50)

    class Meta:
        app_label = "djangondor"


class AuditTaggedWidget(AuditableUUIDBaseTimestampModel):
    """Test-only model with a UUID pk and a ForeignKey, to exercise both at once."""

    name = models.CharField(max_length=50)
    category = models.ForeignKey(AuditCategory, on_delete=models.CASCADE)

    class Meta:
        app_label = "djangondor"


class AuditLogMixinTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as editor:
            editor.create_model(AuditWidget)
            editor.create_model(AuditCategory)
            editor.create_model(AuditTaggedWidget)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            editor.delete_model(AuditTaggedWidget)
            editor.delete_model(AuditCategory)
            editor.delete_model(AuditWidget)
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user("alice", password="pw")
        self.token = _current_user.set(self.user)
        self.addCleanup(_current_user.reset, self.token)

    def test_create_logs_all_fields_with_no_old_value(self):
        widget = AuditWidget.objects.create(name="a")
        log = AuditLog.objects.get(action=AuditLog.Action.CREATE, object_id=widget.pk)
        self.assertEqual(log.user, self.user)
        self.assertIsNone(log.changes["name"]["old"])
        self.assertEqual(log.changes["name"]["new"], "a")

    def test_update_logs_only_changed_fields(self):
        widget = AuditWidget.objects.create(name="a")
        widget.name = "b"
        widget.save()
        log = AuditLog.objects.get(action=AuditLog.Action.UPDATE, object_id=widget.pk)
        self.assertEqual(log.changes, {"name": {"old": "a", "new": "b"}})

    def test_update_does_not_log_when_only_auto_now_field_changes(self):
        widget = AuditWidget.objects.create(name="a")
        widget.save()
        self.assertFalse(
            AuditLog.objects.filter(action=AuditLog.Action.UPDATE, object_id=widget.pk).exists()
        )

    def test_delete_logs_with_empty_changes(self):
        widget = AuditWidget.objects.create(name="a")
        pk = widget.pk
        widget.delete()
        log = AuditLog.objects.get(action=AuditLog.Action.DELETE, object_id=pk)
        self.assertEqual(log.changes, {})
        self.assertEqual(log.user, self.user)

    def test_plain_bulk_create_is_not_audited(self):
        AuditWidget.objects.bulk_create([AuditWidget(name="a"), AuditWidget(name="b")])
        self.assertFalse(AuditLog.objects.filter(action=AuditLog.Action.CREATE).exists())

    def test_plain_bulk_update_is_not_audited(self):
        widget = AuditWidget.objects.create(name="a")
        AuditLog.objects.all().delete()
        widget.name = "b"
        AuditWidget.objects.bulk_update([widget], ["name"])
        self.assertFalse(AuditLog.objects.filter(action=AuditLog.Action.UPDATE).exists())

    def test_bulk_bulk_create_logs_each_object(self):
        created = bulk.bulk_create(AuditWidget, [AuditWidget(name="a"), AuditWidget(name="b")])
        logs = AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_id__in=[o.pk for o in created])
        self.assertEqual(logs.count(), 2)
        log = logs.get(object_id=created[0].pk)
        self.assertEqual(log.changes["name"], {"old": None, "new": "a"})
        self.assertEqual(log.user, self.user)

    def test_bulk_bulk_update_logs_only_changed_objects(self):
        a = AuditWidget.objects.create(name="a")
        b = AuditWidget.objects.create(name="b")
        AuditLog.objects.all().delete()
        a.name = "a-updated"
        b.name = "b"  # unchanged
        bulk.bulk_update([a, b], ["name"])
        self.assertEqual(
            AuditLog.objects.get(action=AuditLog.Action.UPDATE, object_id=a.pk).changes,
            {"name": {"old": "a", "new": "a-updated"}},
        )
        self.assertFalse(AuditLog.objects.filter(action=AuditLog.Action.UPDATE, object_id=b.pk).exists())

    def test_bulk_bulk_update_keeps_old_value_when_pk_is_passed_as_string(self):
        # regression: e.g. a pk coming from request.POST is a str, while the DB
        # returns an int — the old-value lookup must not depend on pk type matching
        widget = AuditWidget.objects.create(name="a")
        AuditLog.objects.all().delete()
        stringly_pk_obj = AuditWidget(pk=str(widget.pk), name="b")
        bulk.bulk_update([stringly_pk_obj], ["name"])
        log = AuditLog.objects.get(action=AuditLog.Action.UPDATE, object_id=widget.pk)
        self.assertEqual(log.changes, {"name": {"old": "a", "new": "b"}})

    def test_foreign_key_and_uuid_pk_are_tracked_by_id_not_instance(self):
        cat_a = AuditCategory.objects.create(name="a")
        cat_b = AuditCategory.objects.create(name="b")
        widget = AuditTaggedWidget.objects.create(name="w", category=cat_a)
        log = AuditLog.objects.get(action=AuditLog.Action.CREATE, object_id=widget.pk)
        self.assertEqual(log.changes["category_id"], {"old": None, "new": cat_a.pk})

        widget.category = cat_b
        widget.save()
        log = AuditLog.objects.get(action=AuditLog.Action.UPDATE, object_id=widget.pk)
        self.assertEqual(log.changes, {"category_id": {"old": cat_a.pk, "new": cat_b.pk}})
