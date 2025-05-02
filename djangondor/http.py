import re
from urllib.parse import urlparse
from django.shortcuts import render
from django.db.models import QuerySet
from django.core.paginator import Paginator
from typing import Dict, Iterable
from  django.http import HttpRequest, JsonResponse

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
    if data or  (isinstance(data,dict) and kwargs) or is_list:
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
        response=JsonResponse(None,safe=True)
        response.status_code=status
    
    return response



def generate_pagination(request:HttpRequest,items:Iterable,page_number=1,page_size=40,generate_urls=True):
    '''
    Create a page from the given `items` list.
    RETURNS

        `page:QuerySet`, `next_url:str|None`, `count:int`, `prev:str|None`
    '''
    pag=Paginator(items,page_size)
    page=pag.page(page_number)
    page_by1=[]
    lst=page.object_list


    
    url=request.build_absolute_uri()
    next,prev=None,None
    if generate_urls:
        url=re.sub(r'page\=\d*','',url)
        urlp=urlparse(url)
        next= f"{urlp.geturl()}{'&' if urlp.query else '?'}page={page.next_page_number()}" if page.has_next() else None
        prev=f"{urlp.geturl()}{'&' if urlp.query else '?'}page={page.previous_page_number()}" if page.has_previous() else None
    return lst,next,pag.count, prev
