from django import template

register = template.Library()

@register.simple_tag(name="contained")
def contained(
    item,
    collection,
    output_when_true="",
    output_when_false="",
):
    return output_when_true if item in collection else output_when_false


@register.simple_tag(name="replacestr")
def replacestr(string: str, arg: str, replacement: str):
    return string.replace(arg, replacement)
