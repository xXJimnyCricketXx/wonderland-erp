from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def filter_url(context, key, value, clear=None):
    """Builds the href for a dropdown-filter option: sets/removes `key`
    while keeping every other current GET param (search, other filters)
    intact - same idea as sort_url, just for filter dropdowns instead of
    column sort. `clear` optionally drops one more param that no longer
    applies once `key` changes (e.g. a dependent sub-filter)."""
    request = context["request"]
    params = request.GET.copy()
    if value in (None, ""):
        params.pop(key, None)
    else:
        params[key] = value
    if clear:
        params.pop(clear, None)
    params.pop("page", None)
    query = params.urlencode()
    return f"?{query}" if query else "?"
