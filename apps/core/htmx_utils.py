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


def htmx_redirect_fixed(url):
    """Like htmx_redirect, but always to `url`, never the Referer. Use this
    when the current tab/pill isn't reflected in the URL at all (e.g.
    Einstellungen's top-level pills and Referenzdaten's sub-pills are pure
    client-side Bootstrap tabs) - trusting the Referer there just replays
    whatever incomplete URL the browser happened to be on (e.g. plain
    /einstellungen/ with no ?tab=), landing back on the default Stammdaten
    pill instead of staying put. Build the deterministic ?tab=/&modul= target
    explicitly instead."""
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response
