"""Baut das HTML fuer den PDF-Report aus BirthChart + ReportBranding +
InterpretationText/ShortDescription/PlanetHouseText/Kombi-Texten zusammen -
siehe Umsetzungsplan Phase 4.

Dokumentaufbau (siehe Kunden-Vorgabe):
  1. Cover
  2. Inhaltsverzeichnis
  3. je Kapitel: Kapitel-Cover (Zeichen-Bild) + Content-Seite(n)
     (Kurzbeschreibung-Baustein + ausfuehrliche Beschreibung, ggf. weitere
     Bausteine wie "Sonne im X. Haus")
  4. Horoskoprad

Die 5 festen Kapitel:
  1. Die Sonne in {Sonnenzeichen}
  2. Aszendent in {Aszendentzeichen}
  3. {Sonnenzeichen} Aszendent {Aszendentzeichen} (+ Baustein "Sonne im X. Haus")
  4. Mond {Dativ-Wendung, z.B. "im Löwen"}
  5. {Sonnenzeichen} mit Mond in {Mondzeichen}

Jedes Kapitel erscheint nur, wenn dafuer tatsaechlich veroeffentlichter
Inhalt existiert - unvollstaendige Kapitel (z.B. Chart ohne Aszendent, weil
keine Geburtszeit bekannt) werden stillschweigend ausgelassen.

Seitenparitaet (Kapitel muessen auf einer rechten/ungeraden Seite beginnen,
das Dokument muss auf einer geraden Seite enden) laeuft komplett ueber CSS
break-before:right/left in report.html - siehe dort."""

import base64

from django.conf import settings
from django.template.loader import render_to_string

from ..models import (
    InterpretationText, Planet, PlanetHouseText, ReportBranding, ShortDescription,
    SonneAszendentKombiText, SonneMondKombiText, ThemenBild,
)
from .chart_image import render_chart_wheel_svg
from .text_render import render_body, render_short_description_html, render_sonne_mond_kombi_html

SUNDAY_FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "sunday" / "Sunday.ttf.woff"
INTER_FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "inter" / "inter.18pt-medium.ttf"
CANVA_SANS_FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "canva sans" / "Canva-Sans-Regular.ttf.woff"
CANVA_SANS_BOLD_FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "canva sans" / "Canva-Sans-Bold.ttf.woff"

TEXT_TYPE_ORDER = [key for key, _ in InterpretationText.TEXT_TYPES]

# ThemenBild ist planetenunabhaengig (siehe Modell-Docstring) - erscheint
# also identisch am Ende des "beziehung"/"kindheit"-Abschnitts, egal ob
# Sonne, Aszendent oder Mond.
TEXT_TYPE_THEMENBILD_TOPIC = {
    "beziehung": "liebe",
    "kindheit": "kind",
}


def _font_base64(path):
    return base64.b64encode(path.read_bytes()).decode()


def _themenbild_html(topic):
    """Bleibt im normalen Textfluss (auf derselben Seite wie der zugehoerige
    Abschnitt, direkt darunter) - der anschliessende Seitenumbruch wird
    separat angehaengt, siehe TEXT_TYPE_THEMENBILD_TOPIC-Aufruferstelle."""
    bild = ThemenBild.objects.filter(topic=topic).first()
    if not bild or not bild.image_data:
        return None
    image_b64 = base64.b64encode(bytes(bild.image_data)).decode()
    return f'<img src="data:{bild.content_type};base64,{image_b64}" class="themenbild-inline">'


def _short_description_html(planet_key, sign, published_only=True):
    planet = Planet.objects.filter(key=planet_key).first()
    if not planet:
        return None
    qs = ShortDescription.objects.filter(planet=planet, sign=sign)
    if published_only:
        qs = qs.filter(status="published")
    short_description = qs.first()
    return render_short_description_html(short_description) if short_description else None


def _render_planet_sign_chapter(planet_key, sign, published_only=True):
    """Sammelt alle (veroeffentlichten) InterpretationText-Abschnitte fuer
    Planet+Zeichen (in TEXT_TYPES-Reihenfolge) und rendert sie mit einer
    Unterueberschrift je Abschnitt. None, wenn nichts vorhanden ist.
    published_only=False fuer die Redaktions-Vorschau (siehe
    build_chapter_preview_pdf) - da soll auch unveroeffentlichter Entwurfs-
    Text sichtbar sein, damit man das GESAMTE geplante Kapitel im
    Seitenfluss pruefen kann, nicht nur den bereits live geschalteten Teil."""
    planet = Planet.objects.filter(key=planet_key).first()
    if not planet or not sign:
        return None
    qs = InterpretationText.objects.filter(planet=planet, sign=sign)
    if published_only:
        qs = qs.filter(status="published")
    texts_by_type = {text.text_type: text for text in qs}
    if not texts_by_type:
        return None

    parts = []
    for text_type in TEXT_TYPE_ORDER:
        text = texts_by_type.get(text_type)
        if not text:
            continue
        if text.heading:
            parts.append(f"<h2>{text.heading}</h2>")
        parts.append(render_body(text.body))
        topic = TEXT_TYPE_THEMENBILD_TOPIC.get(text_type)
        if topic:
            themenbild_html = _themenbild_html(topic)
            if themenbild_html:
                # Erzwingt danach einen Seitenumbruch (dieselbe Klasse wie
                # der [pagebreak]-Marker, siehe report.html/chapter_preview.
                # html), damit der naechste Abschnitt nicht noch auf
                # derselben, schon vom Bild ausgefuellten Seite anfaengt -
                # sonst muesste die Redaktion das manuell nachpflegen.
                parts.append(themenbild_html)
                parts.append('<div class="pagebreak-marker"></div>')
    return "".join(parts)


def _planet_house_html(planet_key, house, published_only=True):
    if not house:
        return None
    planet = Planet.objects.filter(key=planet_key).first()
    if not planet:
        return None
    qs = PlanetHouseText.objects.filter(planet=planet, house=house)
    if published_only:
        qs = qs.filter(status="published")
    text = qs.first()
    if not text:
        return None
    planet_label = planet.name_de
    return f"<h2>{planet_label} im {house.number}. Haus</h2>" + render_body(text.body)


def build_planet_sign_chapter_preview(planet_key, sign):
    """Baut Ueberschrift + kompletten Kapitel-Inhalt (Kurzbeschreibung +
    alle Interpretationstext-Bausteine, in echter Reihenfolge aneinander-
    gehaengt) fuer Planet+Zeichen - fuer die Redaktions-Seitenumbruch-
    Vorschau, siehe admin.py. Ignoriert den Status (auch Entwuerfe), damit
    das ganze geplante Kapitel sichtbar ist."""
    headings = {
        "sonne": f"Die Sonne in {sign.name_de}",
        "aszendent": f"Aszendent in {sign.name_de}",
        "mond": f"Mond {sign.dative_phrase or ('in ' + sign.name_de)}",
    }
    planet = Planet.objects.filter(key=planet_key).first()
    heading = headings.get(planet_key, f"{planet.name_de if planet else planet_key} in {sign.name_de}")
    content_html = "".join(html for html in [
        _short_description_html(planet_key, sign, published_only=False),
        _render_planet_sign_chapter(planet_key, sign, published_only=False),
    ] if html)
    return heading, content_html


def _zodiac_image(sign):
    """Bevorzugt SVG (verlustfrei skalierbar) vor PNG fuers Kapitel-Cover."""
    if not sign:
        return None, None
    if sign.zodiac_image_svg:
        return base64.b64encode(bytes(sign.zodiac_image_svg)).decode(), "image/svg+xml"
    if sign.zodiac_image_png:
        return base64.b64encode(bytes(sign.zodiac_image_png)).decode(), "image/png"
    return None, None


def _build_chapters(chart):
    chapters = []

    def add_chapter(anchor_id, heading, cover_sign, blocks_html):
        blocks_html = [html for html in blocks_html if html]
        if not blocks_html:
            return
        image_base64, image_content_type = _zodiac_image(cover_sign)
        chapters.append({
            "anchor_id": anchor_id,
            "heading": heading,
            "cover_image_base64": image_base64,
            "cover_image_content_type": image_content_type,
            "content_html": "".join(blocks_html),
        })

    if chart.sun_sign:
        add_chapter(
            "sonne", f"Die Sonne in {chart.sun_sign.name_de}", chart.sun_sign,
            [_short_description_html("sonne", chart.sun_sign), _render_planet_sign_chapter("sonne", chart.sun_sign)],
        )

    if chart.ascendant_sign:
        add_chapter(
            "aszendent", f"Aszendent in {chart.ascendant_sign.name_de}", chart.ascendant_sign,
            [_short_description_html("aszendent", chart.ascendant_sign), _render_planet_sign_chapter("aszendent", chart.ascendant_sign)],
        )

    if chart.sun_sign and chart.ascendant_sign:
        kombi = SonneAszendentKombiText.objects.filter(
            sign_sonne=chart.sun_sign, sign_aszendent=chart.ascendant_sign, status="published"
        ).first()
        add_chapter(
            "sonne-aszendent-kombi",
            f"{chart.sun_sign.name_de} Aszendent {chart.ascendant_sign.name_de}",
            chart.ascendant_sign,
            [render_body(kombi.body) if kombi else None, _planet_house_html("sonne", chart.sun_house)],
        )

    if chart.moon_sign:
        phrase = chart.moon_sign.dative_phrase or f"in {chart.moon_sign.name_de}"
        add_chapter(
            "mond", f"Mond {phrase}", chart.moon_sign,
            [_short_description_html("mond", chart.moon_sign), _render_planet_sign_chapter("mond", chart.moon_sign)],
        )

    if chart.sun_sign and chart.moon_sign:
        kombi = SonneMondKombiText.objects.filter(
            sign_sonne=chart.sun_sign, sign_mond=chart.moon_sign, status="published"
        ).first()
        add_chapter(
            "sonne-mond-kombi",
            f"{chart.sun_sign.name_de} mit Mond in {chart.moon_sign.name_de}",
            chart.moon_sign,
            [render_sonne_mond_kombi_html(kombi) if kombi else None],
        )

    return chapters


def build_report_html(chart, *, force_chapters=None):
    branding = ReportBranding.objects.first()
    cover_bg_base64 = None
    if branding and branding.image_data:
        cover_bg_base64 = base64.b64encode(bytes(branding.image_data)).decode()

    chapters = force_chapters if force_chapters is not None else _build_chapters(chart)

    chart_wheel_svg = None
    if chart.birth_time:
        try:
            # resolve_css_variables=True: kerykeion definiert seine
            # Themefarben ausschliesslich ueber CSS custom properties
            # (var(--...)), die weasyprint nicht aufloest - ohne das wuerde
            # das Rad als schwarzer Kreis rendern, siehe chart_image.py.
            chart_wheel_svg = render_chart_wheel_svg(
                birth_date=chart.birth_date, birth_time=chart.birth_time,
                lat=chart.birth_lat, lon=chart.birth_lon, tz_str=chart.birth_timezone,
                house_system=chart.house_system, city=chart.birth_place_raw,
                name=chart.label or "Horoskop", theme="dark-high-contrast",
                resolve_css_variables=True,
            )
        except Exception:
            chart_wheel_svg = None

    # Nur der eigentliche Ortsname, nicht "Ort, Bundesland, Land" (so wie es
    # die GeoNames-Autocomplete in birth_place_raw ablegt).
    birth_place_short = chart.birth_place_raw.split(",")[0].strip()

    return render_to_string("astro/report/report.html", {
        "chart": chart,
        "birth_place_short": birth_place_short,
        "sunday_font_base64": _font_base64(SUNDAY_FONT_PATH),
        "inter_font_base64": _font_base64(INTER_FONT_PATH),
        "canva_sans_font_base64": _font_base64(CANVA_SANS_FONT_PATH),
        "canva_sans_bold_font_base64": _font_base64(CANVA_SANS_BOLD_FONT_PATH),
        "cover_bg_base64": cover_bg_base64,
        "cover_bg_content_type": branding.content_type if branding else "image/png",
        "chapters": chapters,
        "chart_wheel_svg": chart_wheel_svg,
    })


def build_report_pdf(chart):
    from .renderer import render_report_pdf_even_pages

    html_string = build_report_html(chart)
    return render_report_pdf_even_pages(html_string)


def build_chapter_preview_pdf(heading, content_html):
    """Rendert EIN Kapitel (Kopfzeile + Fliesstext, ohne Cover/Inhalts-
    verzeichnis/Kapitel-Cover/Horoskoprad) durch dieselbe @page-content-page-
    CSS und denselben weasyprint-Renderer wie der echte Report - damit die
    Redaktion sieht, wo echte Seitenumbrueche faellen (z.B. mitten in einem
    Absatz), wenn mehrere Bausteine aneinandergehaengt werden. Nutzt bewusst
    ein eigenes, schlankes Template statt report.html, damit kein Chart noetig
    ist und keine Cover/ToC-Seiten die Vorschau aufblaehen."""
    from weasyprint import HTML

    html_string = render_to_string("astro/report/chapter_preview.html", {
        "heading": heading,
        "content_html": content_html,
        "canva_sans_font_base64": _font_base64(CANVA_SANS_FONT_PATH),
        "canva_sans_bold_font_base64": _font_base64(CANVA_SANS_BOLD_FONT_PATH),
        "inter_font_base64": _font_base64(INTER_FONT_PATH),
    })
    return HTML(string=html_string).write_pdf()
