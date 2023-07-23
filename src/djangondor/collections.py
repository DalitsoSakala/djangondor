from typing import Dict
from django.db.models import QuerySet

def dict_values(target:Dict,*fields):
    '''
    Retrieve a list of items specified by `*fields` on the `target` dictionary.
    The list is packed in the same order as the fields are provided
    '''
    lst=[]
    for field in fields:
        lst.append(target[field])
    return lst


def value_list(queryset:QuerySet, field: str):
    '''
    Generate an actual value list of one item per entry.
    This is meant to make it easier to retrieve list of items
    from `queryset` and we want an item
    '''
    return list(map(lambda p: p[0], list(queryset.values_list(field))))