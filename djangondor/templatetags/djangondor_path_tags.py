from typing import Any, Dict
from django import template
from django.urls.resolvers import ResolverMatch

register = template.Library()


@register.simple_tag(name="active_path", takes_context=True)
def active_path(
    context: Dict[str, Any],
    path_name: str,
    output_when_true="active",
    output_when_false="",
):
    match: ResolverMatch = context.request.resolver_match
    is_matched = False
    if ":" in path_name:
        data = path_name.split(":")
        is_matched = match.app_name == data[0] and match.url_name == data[1]
    else:
        is_matched = path_name == match.url_name

    return output_when_true if is_matched else output_when_false


@register.simple_tag(name="active_path_in", takes_context=True)
def active_path_in(
    context: Dict[str, Any],
    *path_names: str,
    output_when_true="active",
    output_when_false="",
):
    match: ResolverMatch = context.request.resolver_match
    is_matched = False
    
    for path in path_names:
        if ":" in path:
            data = path.split(":")
            is_matched = match.app_name == data[0] and match.url_name == data[1]
        else:
            is_matched = path == match.url_name
        if is_matched: break

    return output_when_true if is_matched else output_when_false


@register.simple_tag(name="active_app", takes_context=True)
def active_app(
    context: Dict[str, Any],
    app_name: str,
    output_when_true="active",
    output_when_false="",
):
    return (
        output_when_true
        if context.request.resolver_match.app_name == app_name
        else output_when_false
    )
