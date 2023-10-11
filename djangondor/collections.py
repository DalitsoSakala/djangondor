from typing import Dict
from django.db.models import QuerySet


def dict_values(target: Dict, *fields):
    """
    Retrieve a list of items specified by `*fields` on the `target` dictionary.
    The list is packed in the same order as the fields are provided
    """
    lst = []
    for field in fields:
        lst.append(target.get(field))
    return lst


def list_join(data:list):
    '''Return a string representation of a list with each entry seperated by `,`'''
    builder=''
    for i in data:
        builder+=f'{i},'
    return builder


def get_attrs(data,*attrs:str):
    '''Get all attributes `attrs` found on an object `data`'''
    result=[]
    for attr in attrs:
        result.append(getattr(data,attr))
    return result

def value_list(queryset: QuerySet, field: str):
    """
    Generate an actual value list of one item per entry.
    This is meant to make it easier to retrieve list of items
    from `queryset` and we want an item
    """
    return list(map(lambda p: p[0], list(queryset.values_list(field))))


def exclude(source: Dict, *fields_to_exclude: any) -> Dict:
    '''Eclude the fields specified in `fields_to_exclude` from `source`'''
    return {k: v for k, v in source.items() if k not in fields_to_exclude}
