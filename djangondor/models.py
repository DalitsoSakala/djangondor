from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import JSONField,Func
import uuid

from .middleware import get_current_user

# Create your models here.


# NULLABLE
# USAGE
# =====
# description = models.CharField(max_length=200,**NULLABLE)
# # is the same as:
# description = models.CharField(max_length=200,null=True,default=None,blank=True)
NULLABLE = {"null": True, "default": None, "blank": True}
NULLABLE_CHARFIELD = {**NULLABLE, "max_length": 250}
NULLABLE_FK = {**NULLABLE, "on_delete":models. SET_NULL}
NON_NULL_BLANK_CHARFIELD = {"blank":True, "max_length": 225}


# UUID_PK
# USAGE
# =====
# id=models.UUIDField(**UUID_PK)
# # is the same as:
# id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
UUID_PK = {"primary_key": True, "default": uuid.uuid4, "editable": False}


def make_choices(*entries):
    """Make choices to passed to model field `choices` attribute. Each entry has the form `(entry,entry)`"""
    return [(value, value) for value in entries]

def check_if_tables_exist(*table_names: str):
    '''Check if tables exist in the database'''
    from django.db import connection

    all_tables = connection.introspection.table_names()
    tables = set(table_names)
    return len(tables.intersection(all_tables)) == len(tables)

class BaseTimestampModel(models.Model):
    """Inherit this model to add time stamps to your models"""

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True
        ordering = ("updated_at",)


class UUIDBaseTimestampModel(BaseTimestampModel):
    """Inherit this model to add have a uuid pk andtimestamp"""

    id = models.UUIDField(**UUID_PK)

    class Meta:
        abstract = True


class AuditLog(BaseTimestampModel):
    """A record of a single create/update/delete made to a model that inherits
    `AuditLogMixin`. `changes` holds `{field: {"old": ..., "new": ...}}` for the
    fields that changed (empty for deletes)."""

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=250)
    content_object = GenericForeignKey("content_type", "object_id")

    action = models.CharField(max_length=10, choices=Action.choices)
    changes = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, **NULLABLE_FK)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.get_action_display()} {self.content_type} #{self.object_id}"


def _model_tracked_fields(model):
    # .attname, not .name: for a ForeignKey, .name is e.g. "customer" and getattr()
    # on it returns the related *instance* (not JSON-serializable, and not what
    # .values() returns for the same field) — .attname is "customer_id" on both sides
    # auto_now fields (e.g. `updated_at`) change on every save and would
    # otherwise show up as noise in every diff
    return [f.attname for f in model._meta.fields if f.attname != "id" and not getattr(f, "auto_now", False)]


class AuditLogMixin(models.Model):
    """Inherit this to have every `save()`/`delete()` recorded to `AuditLog`: who did
    it, which fields changed (old and new values) and when. Requires
    `djangondor.middleware.CurrentUserMiddleware` to be installed to know who "who" is;
    without it every entry is logged with `user=None`.

    Limitation: this only hooks `Model.save()`/`Model.delete()`. Bulk operations
    (`QuerySet.bulk_create`, `bulk_update`, `update`, `delete`) go straight to SQL and
    never call either method, so they are **not** audited by this mixin alone. Use
    `djangondor.bulk.bulk_create`/`bulk_update` for audited equivalents of the two bulk
    manager methods.
    """

    class Meta:
        abstract = True

    def _tracked_fields(self):
        return _model_tracked_fields(type(self))

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old = (
            {}
            if is_new
            else type(self).objects.filter(pk=self.pk).values(*self._tracked_fields()).first() or {}
        )
        super().save(*args, **kwargs)
        new = {field: getattr(self, field) for field in self._tracked_fields()}
        if is_new:
            changes = {field: {"old": None, "new": value} for field, value in new.items()}
        else:
            changes = {
                field: {"old": old.get(field), "new": value}
                for field, value in new.items()
                if old.get(field) != value
            }
        if changes:
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                action=AuditLog.Action.CREATE if is_new else AuditLog.Action.UPDATE,
                changes=changes,
                user=get_current_user(),
            )

    def delete(self, *args, **kwargs):
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            action=AuditLog.Action.DELETE,
            changes={},
            user=get_current_user(),
        )
        super().delete(*args, **kwargs)


class AuditableBaseTimestampModel(AuditLogMixin, BaseTimestampModel):
    """`BaseTimestampModel` with automatic audit logging of every save/delete"""

    class Meta:
        abstract = True
        ordering = ("updated_at",)


class AuditableUUIDBaseTimestampModel(AuditLogMixin, UUIDBaseTimestampModel):
    """`UUIDBaseTimestampModel` with automatic audit logging of every save/delete"""

    class Meta:
        abstract = True


class JSONBuildObject(Func):
    """
    Build a new JSON object based on the given keys and values (alternating).
    ```python
        # Example usage
        MyModel.objects.update(data=JSONConcat(
            F('data'),
            JSONBuildObject(
                Value('NAME'),  # key
                F('name'),  # value
            )
        ))
```
    """
    output_field = JSONField()
    function = 'jsonb_build_object'


class JSONConcat(Func):
    """
    Merge all the given JSON objects together, returning a new one.
    
    ```python
        # Example usage
        MyModel.objects.update(data=JSONConcat(
            F('data'),
            JSONBuildObject(
                Value('NAME'),  # key
                F('name'),  # value
            )
        ))
```
    """
    output_field = JSONField()
    arg_joiner = ' || '
    template = '(%(expressions)s)'
