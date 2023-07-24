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


# UUID_PK
# USAGE
# =====
# id=models.UUIDField(**UUID_PK)
# # is the same as:
# id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
UUID_PK = {"primary_key": True, "default": uuid.uuid4, "editable": False}


class BaseTimestampModel(models.Model):
    '''Inherit this model to add time stamps to your models'''
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True
