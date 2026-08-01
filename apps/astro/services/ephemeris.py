"""Berechnet ein Geburtshoroskop aus (Datum, Zeit, Koordinaten, Zeitzone).

Nutzt kerykeion (kapselt Swiss Ephemeris) fuer die zehn klassischen Planeten,
Chiron, Haeuser, Achsenpunkte (Aszendent/MC) und den wahren Mondknoten.
kerykeion liefert dabei allerdings nur die *mittlere* Lilith-Position und kein
Pholus - fuer beides ruft dieses Modul pyswisseph direkt auf, auf denselben
Ephemeriden-Dateien, die kerykeion selbst mitbringt (siehe
_configure_swisseph_path). Gegen zwei Referenzfaelle (22.08.1987, 11:05 und
27.06.2023, 00:16, jeweils Bad Kreuznach: 49.8414 N, 7.86713 O) sind alle
Werte (inkl. wahrer Lilith, Pholus, Mondknoten und Retrograd-Kennzeichnung)
auf die Bogenminute genau geprueft."""

import json
import os
from dataclasses import dataclass

import swisseph as swe
from kerykeion import AstrologicalSubject

_swisseph_configured = False


def _configure_swisseph_path():
    global _swisseph_configured
    if _swisseph_configured:
        return
    import kerykeion as _kerykeion_pkg

    ephe_path = os.path.join(os.path.dirname(_kerykeion_pkg.__file__), "sweph")
    swe.set_ephe_path(ephe_path)
    _swisseph_configured = True


SIGN_KEYS_BY_INDEX = [
    "widder", "stier", "zwillinge", "krebs", "loewe", "jungfrau",
    "waage", "skorpion", "schuetze", "steinbock", "wassermann", "fische",
]

# kerykeion's 3-Buchstaben-Zeichenkuerzel -> unsere ZodiacSign.key-Slugs
SIGN_KEY_BY_KERYKEION_ABBR = {
    "Ari": "widder", "Tau": "stier", "Gem": "zwillinge", "Can": "krebs",
    "Leo": "loewe", "Vir": "jungfrau", "Lib": "waage", "Sco": "skorpion",
    "Sag": "schuetze", "Cap": "steinbock", "Aqu": "wassermann", "Pis": "fische",
}

KERYKEION_HOUSE_ATTRS = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]

KERYKEION_HOUSE_NAME_TO_NUMBER = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}

# unser Planet.key -> kerykeion-Attributname
KERYKEION_PLANET_ATTRS = {
    "sonne": "sun", "mond": "moon", "merkur": "mercury", "venus": "venus",
    "mars": "mars", "jupiter": "jupiter", "saturn": "saturn",
    "uranus": "uranus", "neptun": "neptune", "pluto": "pluto",
    "chiron": "chiron",
}

HOUSE_SYSTEM_CODES = {
    "placidus": "P", "koch": "K", "equal": "A", "whole_sign": "W",
}


def _sign_key_from_longitude(longitude):
    return SIGN_KEYS_BY_INDEX[int(longitude % 360 // 30)]


def _house_number_for_longitude(longitude, house_cusps):
    """house_cusps: die 12 Hausspitzen (ekliptikale Laenge, Index 0 = Haus 1).
    Ordnet longitude dem Haus zu, in dessen Intervall [cusp_n, cusp_n+1) sie
    liegt - inkl. Sonderfall, wenn das Intervall die 0-Grad-Grenze ueberquert."""
    longitude = longitude % 360
    for i in range(12):
        start = house_cusps[i] % 360
        end = house_cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= longitude < end:
                return i + 1
        elif longitude >= start or longitude < end:
            return i + 1
    return 12


@dataclass
class PointResult:
    key: str
    sign_key: str
    longitude: float
    house_number: int = None
    retrograde: bool = False


@dataclass
class ChartResult:
    points: dict
    house_cusps: list
    ascendant_sign_key: str
    mc_sign_key: str
    raw: dict


def compute_chart(
    birth_date, birth_time, lat, lon, tz_str,
    house_system="placidus",
    include_chiron=True, include_pholus=True, include_lilith=True,
    city="",
):
    """birth_time=None -> Berechnung ohne Haeuser/Aszendent (Sonne/Mond/
    Planeten nur nach Zeichen, kein Haussystem moeglich ohne Uhrzeit)."""
    _configure_swisseph_path()

    has_time = birth_time is not None
    hour = birth_time.hour if has_time else 12
    minute = birth_time.minute if has_time else 0
    hsys_code = HOUSE_SYSTEM_CODES.get(house_system, "P")

    subject = AstrologicalSubject(
        "Chart", birth_date.year, birth_date.month, birth_date.day, hour, minute,
        lng=lon, lat=lat, tz_str=tz_str, city=city or "Unbekannt",
        # nation defaultet in kerykeion sonst stillschweigend auf "GB" -
        # deutschsprachiger Shop, andere Herkunftslaender aktuell nicht erfasst.
        nation="DE",
        houses_system_identifier=hsys_code,
        online=False,
        disable_chiron=not include_chiron,
    )

    house_cusps = [getattr(subject, attr).abs_pos for attr in KERYKEION_HOUSE_ATTRS] if has_time else []

    points = {}
    for our_key, keryk_attr in KERYKEION_PLANET_ATTRS.items():
        if our_key == "chiron" and not include_chiron:
            continue
        p = getattr(subject, keryk_attr)
        points[our_key] = PointResult(
            key=our_key,
            sign_key=SIGN_KEY_BY_KERYKEION_ABBR[p.sign],
            longitude=p.abs_pos,
            house_number=KERYKEION_HOUSE_NAME_TO_NUMBER.get(p.house) if has_time else None,
            retrograde=p.retrograde,
        )

    ascendant_sign_key = SIGN_KEY_BY_KERYKEION_ABBR[subject.first_house.sign] if has_time else ""
    mc_sign_key = SIGN_KEY_BY_KERYKEION_ABBR[subject.tenth_house.sign] if has_time else ""

    # Wahre Lilith und Pholus: kerykeion kennt nur die mittlere Lilith und gar
    # kein Pholus, deshalb hier direkt via pyswisseph auf demselben Julian Day
    # (subject.julian_day - identisch mit dem, was kerykeion selbst intern
    # verwendet, siehe Modul-Docstring). calc_ut liefert Laenge + Geschwindigkeit
    # in Laenge (Index 3) - negative Geschwindigkeit = ruecklaeufig (R).
    if has_time:
        jd_ut = subject.julian_day
        if include_lilith:
            pos = swe.calc_ut(jd_ut, swe.OSCU_APOG)[0]
            points["lilith"] = PointResult(
                key="lilith",
                sign_key=_sign_key_from_longitude(pos[0]),
                longitude=pos[0],
                house_number=_house_number_for_longitude(pos[0], house_cusps),
                retrograde=pos[3] < 0,
            )
        if include_pholus:
            pos = swe.calc_ut(jd_ut, swe.PHOLUS)[0]
            points["pholus"] = PointResult(
                key="pholus",
                sign_key=_sign_key_from_longitude(pos[0]),
                longitude=pos[0],
                house_number=_house_number_for_longitude(pos[0], house_cusps),
                retrograde=pos[3] < 0,
            )

        # Mondknoten (wahrer/true node): kerykeion's direkter Attribut-Zugriff
        # (subject.true_north_lunar_node) liefert in dieser kerykeion-Version
        # None, obwohl der Wert berechnet wird - deshalb ueber subject.json()
        # ausgelesen, wo er korrekt vorhanden ist.
        node_data = json.loads(subject.json())["true_north_lunar_node"]
        points["mondknoten"] = PointResult(
            key="mondknoten",
            sign_key=SIGN_KEY_BY_KERYKEION_ABBR[node_data["sign"]],
            longitude=node_data["abs_pos"],
            house_number=KERYKEION_HOUSE_NAME_TO_NUMBER.get(node_data["house"]),
            retrograde=node_data.get("retrograde", False),
        )

    raw = {
        "points": {
            key: {
                "sign": point.sign_key,
                "longitude": point.longitude,
                "house": point.house_number,
                "retrograde": point.retrograde,
            }
            for key, point in points.items()
        },
        "house_cusps": house_cusps,
        "ascendant_sign": ascendant_sign_key,
        "mc_sign": mc_sign_key,
        "house_system": house_system,
        "julian_day": subject.julian_day,
    }

    return ChartResult(
        points=points,
        house_cusps=house_cusps,
        ascendant_sign_key=ascendant_sign_key,
        mc_sign_key=mc_sign_key,
        raw=raw,
    )
