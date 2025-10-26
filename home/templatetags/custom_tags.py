from django import template

register = template.Library()

@register.filter
def get_range(value):
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(1, 6)  # Default to 5 ranks