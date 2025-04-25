from django.shortcuts import render
from django.db.models import QuerySet
from typing import Dict
from  django.http import JsonResponse

# Create your views here.

def json_response(data:list|tuple|QuerySet|Dict|str=None,status=None,meta=None,next:str=None,prev:str=None,count=None,**kwargs):
    '''Generates a JSONResponse
    * When `data` is an instance of `list` a response with
    {count, and results} is returned
    * When `data` is a str, an error response is returned
    with {error}
    * When data is `None` or no argument is passed, a blank response is returned
    '''
    is_list=isinstance(data,(list,tuple,set,QuerySet))
    if data or (meta and is_list) or (isinstance(data,dict) and kwargs):
        is_error=isinstance(data,str)
        
        response=JsonResponse(
            {
                'count':count or len(list(data)),
                'results':list(data),
                'meta':meta,
                'next':next,
                'previous':prev,
            }
            if is_list\
            else {'error':data} if is_error else \
                {**data,**kwargs} if isinstance(data,dict) else data
        )
        response.status_code=status or 400 if is_error else status or 200
    else:
        response=JsonResponse()
        response.status_code=status
    
    return response

