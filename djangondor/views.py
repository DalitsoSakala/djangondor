from typing import Dict, Generic, TypeVar
from django.db.models import QuerySet,Count
import types

T=TypeVar('T')
class SortingMixin(Generic[T]):
    """Overrides the `filter_queryset` method"""

    sorting_aliases: Dict[str, str | list | tuple] = {}

    def filter_queryset(self, queryset)->QuerySet[T]:
        queryset: QuerySet[T]= super().filter_queryset(queryset)
        sorting: str = self.request.GET.get("sorting")
        if len(sorting or ''):
            try:
                def sort_and_return(queryset:QuerySet,sorting:str):
                    pks=list(queryset.order_by('pk').distinct('pk').values_list('pk',flat=True))
                    qs=queryset.model.objects.filter(pk__in=pks).order_by(sorting)
                    return qs.distinct()
                aliases = self.sorting_aliases
                for k, v in aliases.items():
                    neutral = sorting.replace("-", "")
                    prefix = neutral != sorting and "-" or ""

                    if isinstance(v, (list, tuple)) and k == neutral:
                        if isinstance(v[1],types.FunctionType):
                            return v[1](queryset).order_by(f'{prefix}{v[0]}')
                        return sort_and_return(queryset.alias(**{v[0]: v[1]}),f"{prefix}{v[0]}")
                    if k == neutral:
                        sorting = f"{prefix}{v}"
                    break
                sorting = sorting.replace(".", "__")
                return sort_and_return(queryset,sorting)
            except Exception as e:
                ...
        return queryset


class ViewsetPropsMixin(Generic[T]):
    @property
    def filtered_qs(self)->QuerySet[T]:
        return self.filter_queryset(self.get_queryset())
    
    
    @property
    def qs(self)->QuerySet[T]:
        return self.get_queryset()