"""HTML -> PDF via weasyprint - siehe Umsetzungsplan Phase 4."""

from weasyprint import HTML


def render_report_pdf(html_string):
    return HTML(string=html_string).write_pdf()


def render_report_pdf_even_pages(html_string):
    """Rendert einmal, um die tatsaechliche Seitenzahl zu ermitteln, und
    haengt bei Bedarf eine Leerseite an, damit das Dokument auf einer
    geraden Seitenzahl endet (Druck-/Bindungsvorgabe). Ein reiner CSS-Trick
    (break-before:left auf einem Fuellelement) waere hier nicht zuverlaessig
    genug - siehe Testrecherche: erzwingt teils einen zusaetzlichen,
    unnoetigen Seitenumbruch, statt "schon richtig" korrekt zu erkennen."""
    document = HTML(string=html_string).render()
    if len(document.pages) % 2 == 0:
        return document.write_pdf()

    filler_html = html_string.replace(
        "</body>", '<div style="page-break-before: always;"></div></body>', 1
    )
    return HTML(string=filler_html).render().write_pdf()
