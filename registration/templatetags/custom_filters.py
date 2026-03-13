from django import template

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """Template filter to lookup dictionary values by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def get_dict_item(dictionary, key):
    """Alternative name for dict lookup filter"""
    return dict_lookup(dictionary, key)