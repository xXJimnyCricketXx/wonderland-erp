"""Orchestriert Geocoding (geocode.py) + Ephemeriden-Berechnung
(ephemeris.py): nimmt Formulareingabe entgegen und erzeugt eine gespeicherte
BirthChart-Instanz."""

from ..models import BirthChart, House, ZodiacSign
from . import ephemeris
from .geocode import geocode_place


def build_birth_chart(
    label="", *, birth_date, birth_time=None, birth_place="",
    lat=None, lon=None, tz_str="", geonameid="",
    house_system="placidus",
    include_chiron=True, include_pholus=True, include_lilith=True,
    chart=None,
):
    """lat/lon/tz_str koennen direkt uebergeben werden (z. B. wenn der Ort
    bereits per GeoNames-Autocomplete im Formular ausgewaehlt wurde) - sonst
    wird birth_place ueber geocode_place() aufgeloest.

    `chart` optional: eine bestehende BirthChart-Instanz zum Aktualisieren
    (Bearbeiten-Funktion) statt eine neue anzulegen."""
    if lat is None or lon is None or not tz_str:
        cached = geocode_place(birth_place)
        lat, lon, tz_str = cached.lat, cached.lon, cached.timezone
        geonameid = geonameid or cached.geonameid
        birth_place = birth_place or cached.name

    result = ephemeris.compute_chart(
        birth_date=birth_date, birth_time=birth_time,
        lat=lat, lon=lon, tz_str=tz_str,
        house_system=house_system,
        include_chiron=include_chiron, include_pholus=include_pholus, include_lilith=include_lilith,
        city=birth_place,
    )

    sign_by_key = {sign.key: sign for sign in ZodiacSign.objects.all()}
    house_by_number = {house.number: house for house in House.objects.all()}

    def sign_for(point_key):
        point = result.points.get(point_key)
        return sign_by_key.get(point.sign_key) if point else None

    def house_for(point_key):
        point = result.points.get(point_key)
        return house_by_number.get(point.house_number) if point and point.house_number else None

    fields = dict(
        label=label,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place_raw=birth_place,
        geonameid=geonameid,
        birth_lat=lat,
        birth_lon=lon,
        birth_timezone=tz_str,
        house_system=house_system,
        include_chiron=include_chiron,
        include_pholus=include_pholus,
        include_lilith=include_lilith,
        sun_sign=sign_for("sonne"),
        sun_house=house_for("sonne"),
        moon_sign=sign_for("mond"),
        moon_house=house_for("mond"),
        ascendant_sign=sign_by_key.get(result.ascendant_sign_key) if result.ascendant_sign_key else None,
        mc_sign=sign_by_key.get(result.mc_sign_key) if result.mc_sign_key else None,
        raw_positions=result.raw,
    )

    if chart is not None:
        for key, value in fields.items():
            setattr(chart, key, value)
        chart.save()
        return chart

    return BirthChart.objects.create(**fields)
