from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_url(context, field):
    """Builds the href for a clickable column header: toggles between
    field / -field, resets to page 1, and keeps all other GET params
    (search, filters) intact."""
    request = context["request"]
    current = request.GET.get("sort", "")
    params = request.GET.copy()
    params["sort"] = f"-{field}" if current == field else field
    params.pop("page", None)
    return "?" + params.urlencode()


@register.simple_tag(takes_context=True)
def sort_icon(context, field):
    current = context["request"].GET.get("sort", "")
    if current == field:
        return "bi-caret-up-fill"
    if current == f"-{field}":
        return "bi-caret-down-fill"
    return "bi-caret-down text-white-50"
