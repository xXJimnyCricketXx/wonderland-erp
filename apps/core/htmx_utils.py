from django.http import HttpResponse


def htmx_redirect(request, fallback_url):
    """204 response + HX-Redirect back to whatever page the user was
    actually on (the Referer HTMX sent along with the save request) rather
    than a hardcoded URL - so saving something doesn't silently reset the
    user's current tab/pill/filter/page back to a fixed default. Falls back
    to `fallback_url` only when there's no Referer at all (e.g. a direct,
    non-browser request)."""
    response = HttpResponse(status=204)
    response["HX-Redirect"] = request.META.get("HTTP_REFERER") or fallback_url
    return response
