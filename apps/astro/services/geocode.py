"""Ortssuche + Zeitzonen-Aufloesung ueber GeoNames (kostenloser Account unter
geonames.org/login, Web-Services muessen dort einmalig freigeschaltet werden
- siehe GEONAMES_USERNAME in settings.py). Liefert Koordinaten und IANA-
Zeitzone in einem Rutsch (zwei GeoNames-Aufrufe: Ortssuche + Zeitzone zu den
gefundenen Koordinaten), zwischengespeichert in GeocodeCache, damit derselbe
Ort (z. B. "Bad Kreuznach") nicht bei jedem Horoskop erneut angefragt wird."""

import requests
from django.conf import settings

from ..models import GeocodeCache

GEONAMES_BASE_URL = "https://secure.geonames.org"
REQUEST_TIMEOUT = 10


class GeocodeError(Exception):
    pass


def geocode_place(place_name):
    place_name = (place_name or "").strip()
    if not place_name:
        raise GeocodeError("Kein Ort angegeben.")

    cached = GeocodeCache.objects.filter(query=place_name).first()
    if cached:
        return cached

    username = settings.GEONAMES_USERNAME
    if not username:
        raise GeocodeError("GEONAMES_USERNAME ist nicht konfiguriert - siehe .env.example.")

    search_resp = requests.get(
        f"{GEONAMES_BASE_URL}/searchJSON",
        params={"q": place_name, "maxRows": 1, "username": username},
        timeout=REQUEST_TIMEOUT,
    )
    search_resp.raise_for_status()
    search_data = search_resp.json()
    if search_data.get("status"):
        raise GeocodeError(f"GeoNames-Fehler: {search_data['status'].get('message')}")

    results = search_data.get("geonames") or []
    if not results:
        raise GeocodeError(f"Kein Ort gefunden für „{place_name}“.")
    result = results[0]
    lat = float(result["lat"])
    lon = float(result["lng"])

    timezone_resp = requests.get(
        f"{GEONAMES_BASE_URL}/timezoneJSON",
        params={"lat": lat, "lng": lon, "username": username},
        timeout=REQUEST_TIMEOUT,
    )
    timezone_resp.raise_for_status()
    timezone_data = timezone_resp.json()

    return GeocodeCache.objects.create(
        query=place_name,
        geonameid=str(result.get("geonameId", "")),
        name=result.get("name", place_name),
        country=result.get("countryName", ""),
        lat=lat,
        lon=lon,
        timezone=timezone_data.get("timezoneId", ""),
    )


def search_places(query, max_rows=5):
    """Fuer die Live-Autocomplete im Formular: mehrere Treffer, ohne
    Zeitzonen-Lookup (der waere pro Vorschlag ein eigener API-Call - zu
    teuer fuer jeden Tastenanschlag). Die Zeitzone wird erst bei der
    tatsaechlichen Auswahl per resolve_timezone() nachgeladen. Liefert eine
    leere Liste statt eines Fehlers (z. B. fehlender Account), damit die
    Autocomplete im Formular einfach nichts anzeigt statt einen JS-Fehler
    auszuloesen - geocode_place() bleibt beim Submit der harte Fallback mit
    echter Fehlermeldung."""
    query = (query or "").strip()
    username = settings.GEONAMES_USERNAME
    if not query or not username:
        return []

    resp = requests.get(
        f"{GEONAMES_BASE_URL}/searchJSON",
        params={
            # name_startsWith statt q: echtes Praefix-Matching fuer
            # Live-Tippen (q findet sonst z.B. "Kreuzberg" vor "Bad
            # Kreuznach" bei "Bad Kreuz"). featureClass=P (nur Orte, keine
            # Verwaltungsgrenzen/Berge) + orderby=population sortiert den
            # tatsaechlich gemeinten (groessten) Ort nach oben.
            "name_startsWith": query, "maxRows": max_rows, "username": username,
            "featureClass": "P", "orderby": "population",
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status"):
        return []

    return [
        {
            "geonameid": str(result.get("geonameId", "")),
            "name": result.get("name", ""),
            "admin": result.get("adminName1", ""),
            "country": result.get("countryName", ""),
            "lat": float(result["lat"]),
            "lon": float(result["lng"]),
        }
        for result in data.get("geonames", [])
    ]


def resolve_timezone(lat, lon):
    username = settings.GEONAMES_USERNAME
    if not username:
        raise GeocodeError("GEONAMES_USERNAME ist nicht konfiguriert - siehe .env.example.")

    resp = requests.get(
        f"{GEONAMES_BASE_URL}/timezoneJSON",
        params={"lat": lat, "lng": lon, "username": username},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("timezoneId", "")
