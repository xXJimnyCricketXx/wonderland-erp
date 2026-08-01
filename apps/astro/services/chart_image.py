"""Erzeugt das grafische Horoskoprad (SVG) via kerykeion - siehe
Umsetzungsplan Phase 3.6. kerykeion berechnet dabei bewusst selbst noch
einmal aus denselben Eingabedaten (statt bereits berechnete BirthChart-Werte
zu injizieren) - einfacher, und beide Berechnungen sind ohnehin identisch
(gleiche Ephemeride, gleiches Häusersystem), siehe ephemeris.py."""

import re
import tempfile
from pathlib import Path

from kerykeion import AstrologicalSubject, KerykeionChartSVG

from .ephemeris import HOUSE_SYSTEM_CODES

CSS_VAR_DECLARATION_RE = re.compile(r"--([\w-]+):\s*([^;]+);")
CSS_VAR_USAGE_RE = re.compile(r"var\(\s*--([\w-]+)(?:,\s*([^)]+))?\s*\)")


def _resolve_svg_css_variables(svg_text):
    """weasyprint kann CSS custom properties (var(--...)) nicht aufloesen,
    kerykeion definiert seine Themefarben aber ausschliesslich darueber -
    ohne das hier wird das Rad in der PDF zum schwarzen Kreis. Loest die
    Variablen manuell auf (nur fuer den PDF-Pfad noetig, im Browser
    funktioniert var() nativ, siehe render_chart_wheel_svg).

    Manche kerykeion-Variablen referenzieren selbst wieder andere Variablen
    (--a: var(--b)) - ein einzelner Ersetzungsdurchlauf wuerde das nur eine
    Ebene tief aufloesen und var(...) fuer verkettete Referenzen stehen
    lassen, deshalb erst das variables-Dict selbst so oft aufloesen, bis
    keine Verkettung mehr uebrig ist, und erst dann auf die ganze SVG anwenden."""
    variables = {name: value.strip() for name, value in CSS_VAR_DECLARATION_RE.findall(svg_text)}

    def replace(match):
        name, fallback = match.group(1), match.group(2)
        return variables.get(name, fallback or "").strip()

    # Bis zu 10 Durchlaeufe reichen fuer jede realistische Verkettungstiefe -
    # danach abbrechen statt in eine Endlosschleife bei zirkulaeren
    # Referenzen zu laufen.
    for _ in range(10):
        variables = {name: CSS_VAR_USAGE_RE.sub(replace, value) for name, value in variables.items()}
        if not any("var(" in value for value in variables.values()):
            break

    return CSS_VAR_USAGE_RE.sub(replace, svg_text)


def render_chart_wheel_svg(
    birth_date, birth_time, lat, lon, tz_str, house_system="placidus", city="",
    name="Horoskop", theme="classic", resolve_css_variables=False,
):
    """Gibt den SVG-Inhalt des Horoskoprads als String zurueck. `theme` steuert
    die kerykeion-Farbwelt. `resolve_css_variables=True` fuer den PDF-Pfad
    (weasyprint), sonst bleiben die var(...)-Referenzen stehen (Browser
    koennen sie direkt, das spart die Vorverarbeitung)."""
    hour = birth_time.hour if birth_time else 12
    minute = birth_time.minute if birth_time else 0

    subject = AstrologicalSubject(
        name, birth_date.year, birth_date.month, birth_date.day, hour, minute,
        lng=lon, lat=lat, tz_str=tz_str, city=city or "Unbekannt",
        # nation defaultet in kerykeion sonst stillschweigend auf "GB".
        nation="DE",
        houses_system_identifier=HOUSE_SYSTEM_CODES.get(house_system, "P"),
        online=False,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        chart_svg = KerykeionChartSVG(subject, new_output_directory=tmp_dir, chart_language="DE", theme=theme)
        chart_svg.makeSVG()
        svg_path = next(Path(tmp_dir).glob("*.svg"))
        svg_text = svg_path.read_text(encoding="utf-8")

    # kerykeion setzt selbst NIRGENDS eine font-family (weder als CSS-
    # Property noch als Attribut) - im Browser wird dadurch stillschweigend
    # dessen Standard-Sans-Serif verwendet (meist eine schmale Schrift wie
    # Arial), weasyprint faellt dagegen auf eine eigene, i.d.R. breitere
    # Fallback-Schrift zurueck. Bei identischem font-size:10px fuer die
    # Infotext-Zeilen (Ort/Koordinaten/Datum) fuehrt das im PDF zu echten
    # Kollisionen mit den Hausgrad-Beschriftungen des Rads, obwohl Browser
    # und PDF dieselbe Geometrie/dasselbe Theme verwenden - verifiziert durch
    # Vergleichsrender mit explizit gesetzter Schrift (Kollision verschwindet
    # vollstaendig). Deshalb hier immer explizit setzen, nicht nur fuer den
    # PDF-Pfad, damit Browser- und PDF-Ansicht garantiert gleich schmal sind.
    svg_text = svg_text.replace(
        "<svg", '<svg style="font-family: Arial, Helvetica, sans-serif;"', 1
    )

    if resolve_css_variables:
        svg_text = _resolve_svg_css_variables(svg_text)
    return svg_text
