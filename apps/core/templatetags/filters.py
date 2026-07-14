from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Django templates have no `dict[var]` syntax - needed for looking up
    quarter_active[q] where q is itself a loop variable, not a literal."""
    return mapping.get(key)


@register.simple_tag(takes_context=True)
def filter_url(context, key, value, clear=None, clear2=None):
    """Builds the href for a dropdown-filter option: sets/removes `key`
    while keeping every other current GET param (search, other filters)
    intact - same idea as sort_url, just for filter dropdowns instead of
    column sort. `clear`/`clear2` optionally drop one or two more params
    that no longer apply once `key` changes (e.g. dependent sub-filters)."""
    request = context["request"]
    params = request.GET.copy()
    if value in (None, ""):
        params.pop(key, None)
    else:
        params[key] = value
    if clear:
        params.pop(clear, None)
    if clear2:
        params.pop(clear2, None)
    params.pop("page", None)
    query = params.urlencode()
    return f"?{query}" if query else "?"


@register.simple_tag(takes_context=True)
def toggle_url(context, key, value):
    """Toggles a single `value` in/out of the comma-separated multi-value
    GET param `key` (used for the Jahr/Monat chip filters), keeping every
    other current GET param intact."""
    request = context["request"]
    params = request.GET.copy()
    current = [v for v in params.get(key, "").split(",") if v]
    value = str(value)
    if value in current:
        current.remove(value)
    else:
        current.append(value)
    if current:
        params[key] = ",".join(current)
    else:
        params.pop(key, None)
    params.pop("page", None)
    query = params.urlencode()
    return f"?{query}" if query else "?"


@register.simple_tag(takes_context=True)
def toggle_quarter_url(context, q):
    """A quarter button toggles its 3 months together in the `monat`
    multi-select: if all 3 are already selected, removes them (quarter
    off); otherwise adds whichever are missing (quarter on). This is a
    shortcut on top of the Monat filter, not a separate filter dimension -
    so Q1+Q2 together just means "these 6 months", no extra state."""
    request = context["request"]
    months = [str((int(q) - 1) * 3 + i) for i in (1, 2, 3)]
    params = request.GET.copy()
    current = [v for v in params.get("monat", "").split(",") if v]
    if all(m in current for m in months):
        current = [v for v in current if v not in months]
    else:
        for m in months:
            if m not in current:
                current.append(m)
    if current:
        params["monat"] = ",".join(current)
    else:
        params.pop("monat", None)
    params.pop("page", None)
    query = params.urlencode()
    return f"?{query}" if query else "?"
