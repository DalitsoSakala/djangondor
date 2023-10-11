from django.db import models
import uuid

# Create your models here.


# NULLABLE
# USAGE
# =====
# description = models.CharField(max_length=200,**NULLABLE)
# # is the same as:
# description = models.CharField(max_length=200,null=True,default=None,blank=True)
NULLABLE = {"null": True, "default": None, "blank": True}
NULLABLE_CHARFIELD = {**NULLABLE, "max_length": 100}


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
