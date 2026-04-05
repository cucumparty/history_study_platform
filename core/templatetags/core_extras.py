"""Custom template filters for the history app."""

from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """Get an item from a dict by key in a template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
