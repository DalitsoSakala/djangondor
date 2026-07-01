from django.contrib.contenttypes.models import ContentType

from .middleware import get_current_user
from .models import AuditLog, _model_tracked_fields


def bulk_create(model, objs, batch_size=None, ignore_conflicts=False):
    """Audited equivalent of `model.objects.bulk_create(objs)`. `bulk_create` inserts
    with a single SQL statement and never calls `save()`, so `AuditLogMixin` can't see
    it on its own — this runs the insert and then writes one `AuditLog` "create" entry
    per object.

    Objects whose primary key isn't populated by the database after insert (e.g.
    auto-increment pk on backends that don't support `RETURNING`) are skipped, since
    there's no id to attach the log entry to.

    Returns whatever `bulk_create` returns.

    Usage — in place of::

        Article.objects.bulk_create(objs)

    use::

        from djangondor import bulk
        bulk.bulk_create(Article, objs)
    """
    created = model.objects.bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts)
    fields = _model_tracked_fields(model)
    content_type = ContentType.objects.get_for_model(model)
    user = get_current_user()
    AuditLog.objects.bulk_create(
        [
            AuditLog(
                content_type=content_type,
                object_id=obj.pk,
                action=AuditLog.Action.CREATE,
                changes={field: {"old": None, "new": getattr(obj, field)} for field in fields},
                user=user,
            )
            for obj in created
            if obj.pk is not None
        ]
    )
    return created


def bulk_update(objs, fields, batch_size=None):
    """Audited equivalent of `Model.objects.bulk_update(objs, fields)`. `bulk_update`
    writes with a single SQL statement and never calls `save()`, so `AuditLogMixin`
    can't see it on its own — this fetches the current values, runs the update, and
    writes one `AuditLog` "update" entry per object that actually changed.

    `objs` must already have their new field values set in memory and their pk
    populated, same requirement as `bulk_update` itself.

    Usage — in place of::

        Article.objects.bulk_update(objs, ["status"])

    use::

        from djangondor import bulk
        bulk.bulk_update(objs, ["status"])
    """
    objs = list(objs)
    if not objs:
        return
    model = type(objs[0])
    tracked = [f for f in fields if f in _model_tracked_fields(model)]
    # keyed by str(pk): objs[].pk may not be the same type the DB returns (e.g. a pk
    # passed in as a string from a form), so compare on string form rather than risk a
    # silent dict-lookup miss that would make every "old" value look like None
    old_by_pk = {
        str(row["pk"]): row
        for row in model.objects.filter(pk__in=[obj.pk for obj in objs]).values("pk", *tracked)
    }
    model.objects.bulk_update(objs, fields, batch_size=batch_size)
    content_type = ContentType.objects.get_for_model(model)
    user = get_current_user()
    logs = []
    for obj in objs:
        old = old_by_pk.get(str(obj.pk), {})
        changes = {
            field: {"old": old.get(field), "new": getattr(obj, field)}
            for field in tracked
            if old.get(field) != getattr(obj, field)
        }
        if changes:
            logs.append(
                AuditLog(
                    content_type=content_type,
                    object_id=obj.pk,
                    action=AuditLog.Action.UPDATE,
                    changes=changes,
                    user=user,
                )
            )
    AuditLog.objects.bulk_create(logs)
