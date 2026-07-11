def resolve_sort(request, allowed_fields, default):
    """Reads ?sort=field (or -field for descending) from the request and
    validates it against a per-view whitelist, so list views can safely pass
    it straight to queryset.order_by() without letting the query string probe
    arbitrary model/relation fields."""
    sort = request.GET.get("sort", "")
    field = sort[1:] if sort.startswith("-") else sort
    if field in allowed_fields:
        return sort
    return default
