"""Markdown-Body-Text -> gesaeubertes HTML fuer den PDF-Report. Nur eine
kleine, feste Tag-Whitelist erlaubt (bleach), damit Redakteure zwar
Markdown-Formatierung nutzen koennen, aber kein beliebiges HTML/Skript in
den Report gelangt."""

import base64
import re

import bleach
import markdown

ALLOWED_TAGS = ["p", "strong", "em", "h1", "h2", "h3", "ul", "ol", "li", "br", "div"]
ALLOWED_ATTRIBUTES = {"div": ["class"]}

SYMBOL_MARKER = "[symbol_image]"
PAGEBREAK_MARKER = "[pagebreak]"
CENTER_RE = re.compile(r"\[center\](.*?)\[/center\]", re.DOTALL)


def _markdown_clean(text):
    return bleach.clean(markdown.markdown(text or ""), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def _render_segment(segment):
    """Rendert ein einzelnes (bereits am [pagebreak]-Marker aufgeteiltes)
    Segment. Der Marker "[center]...[/center]" zentriert den eingeschlossenen
    Abschnitt (z.B. das einleitende Zitat einer Kurzbeschreibung), der Rest
    bleibt wie gewohnt linksbuendig - beide Teile laufen unabhaengig durch
    Markdown/Bleach, damit z.B. **fett** auch innerhalb des Zitats geht."""
    parts = []
    last_end = 0
    for match in CENTER_RE.finditer(segment):
        before = segment[last_end:match.start()]
        if before.strip():
            parts.append(_markdown_clean(before))
        parts.append(f'<div class="zentriert-text">{_markdown_clean(match.group(1))}</div>')
        last_end = match.end()
    remainder = segment[last_end:]
    if remainder.strip() or not parts:
        parts.append(_markdown_clean(remainder))
    return "".join(parts)


def render_body(text):
    """Markdown -> gesaeubertes HTML. Der Marker "[pagebreak]" im
    Redaktionstext erzwingt einen gezielten Seitenumbruch an genau dieser
    Stelle (siehe .pagebreak-marker in report.html) - jedes Segment wird
    separat durch Markdown/Bleach gejagt, der Trenner-Div selbst laeuft NICHT
    durch bleach (fest codiert, kein Redaktionsinput)."""
    segments = (text or "").split(PAGEBREAK_MARKER)
    rendered_segments = [_render_segment(segment) for segment in segments]
    return '<div class="pagebreak-marker"></div>'.join(rendered_segments)


def render_short_description_html(short_description):
    """Ersetzt den Marker "[symbol_image]" im Markdown-Text durch das
    kleine Zeichen-Symbolbild (Base64-inline PNG) - so legt die Redaktion
    per Marker im Fliesstext selbst fest, wo genau das Symbol erscheint."""
    sign = short_description.sign
    img_tag = ""
    if sign.symbol_image_png:
        image_b64 = base64.b64encode(bytes(sign.symbol_image_png)).decode()
        img_tag = f'<img src="data:image/png;base64,{image_b64}" class="zeichen-symbol-inline">'

    before, marker, after = short_description.body.partition(SYMBOL_MARKER)
    html = render_body(before)
    if marker:
        html += img_tag + render_body(after)
    return html


KOMBI_ROW_LABELS = [
    ("charakter", "Dein Charakter"),
    ("lernt", "Du lernst"),
    ("muss", "Du musst"),
    ("liebe", "Liebe"),
    ("astrologik", "Astrologik"),
]


def _ruler_correspondence_row(sign_sonne, sign_mond):
    """Die "Sonne in Widder = Sonne/Mars"-Zeile laesst sich komplett aus
    ZodiacSign.ruler_planet ableiten (siehe Modell) - keine manuelle Eingabe
    noetig. Wie die anderen Inhaltszeilen 2-spaltig (Sonne-Seite links,
    Mond-Seite rechts), nicht als verbundene Zeile. None, falls fuer eines
    der beiden Zeichen kein Herrscherplanet hinterlegt ist."""
    if not sign_sonne.ruler_planet or not sign_mond.ruler_planet:
        return ""
    sonne_line = f"Sonne in {sign_sonne.name_de} = Sonne/{sign_sonne.ruler_planet.name_de}"
    mond_line = f"Mond in {sign_mond.name_de} = Mond/{sign_mond.ruler_planet.name_de}"
    return f'<tr class="kombi-ruler-row"><td>{sonne_line}</td><td>{mond_line}</td></tr>'


def render_sonne_mond_kombi_html(kombi):
    """SonneMondKombiText hat eine Gegenueberstellungs-Tabelle (Sonne/Mond
    je Dein-Charakter/Du-lernst/Du-musst/Liebe/Astrologik) statt eines
    einzelnen Fliesstexts - siehe Modell-Docstring. Nur 2 Inhaltsspalten
    (Sonne/Mond), die Zeilenlabels stehen als verbundene Zeile darueber statt
    in einer eigenen Spalte. Nach dem Einleitungstext (kombi_text) erzwingt
    ein automatischer Seitenumbruch, dass die Tabelle immer auf einer neuen
    Seite beginnt.

    Jedes Label+Inhalt-Paar steckt in einem EIGENEN <tbody> mit
    break-inside:avoid (siehe CSS) - so bleiben "Liebe"-Ueberschrift und ihr
    Inhalt immer zusammen auf einer Seite, statt dass die Ueberschrift am
    Seitenende haengen bleibt und der Inhalt erst auf der naechsten Seite
    folgt."""
    sign_sonne, sign_mond = kombi.sign_sonne, kombi.sign_mond
    groups = []
    for field, label in KOMBI_ROW_LABELS:
        group_rows = (
            f'<tr class="kombi-row-label"><td colspan="2">{label}</td></tr>'
            f"<tr><td>{render_body(getattr(kombi, f'sonne_{field}'))}</td>"
            f"<td>{render_body(getattr(kombi, f'mond_{field}'))}</td></tr>"
        )
        if field == "astrologik":
            group_rows += _ruler_correspondence_row(sign_sonne, sign_mond)
        groups.append(f'<tbody class="kombi-group">{group_rows}</tbody>')

    table = (
        '<h2 class="kombi-heading">Gegenüberstellung der Eigenschaften</h2>'
        '<table class="kombi-table"><thead><tr>'
        f"<th>Sonne in {sign_sonne.name_de}</th><th>Mond in {sign_mond.name_de}</th>"
        f"</tr></thead>{''.join(groups)}</table>"
    )
    return render_body(kombi.kombi_text) + '<div class="pagebreak-marker"></div>' + table
