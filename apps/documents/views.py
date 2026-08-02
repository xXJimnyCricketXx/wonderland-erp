from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View

from finance.models import Expense, Income, TaxReport
from knowledge.models import PackagingLicenseDocument
from orders.models import Order


def _group_by_year(entries, year_of=lambda entry: entry["date"].year if entry["date"] else None):
    """Gruppiert Dateien nach Jahr fuer die Jahres-Unterordner im
    Dokumente-Browser - neuestes Jahr zuerst und vorausgewaehlt aufgeklappt,
    aeltere Jahre eingeklappt, damit lange Listen (z.B. Ausgangsrechnungen
    ueber mehrere Jahre) nicht auf einen Schlag erschlagend wirken.
    year_of ist austauschbar, da nicht ueberall dasselbe Feld das
    "eigentliche" Jahr traegt - bei TaxReport z.B. ist year der Zeitraum,
    den der Bericht abdeckt, nicht das (meist viel spaetere) Uploaddatum."""
    by_year = defaultdict(list)
    for entry in entries:
        by_year[year_of(entry) or "Unbekannt"].append(entry)
    years = sorted((y for y in by_year if isinstance(y, int)), reverse=True)
    groups = [{"year": y, "entries": by_year[y]} for y in years]
    if "Unbekannt" in by_year:
        groups.append({"year": "Unbekannt", "entries": by_year["Unbekannt"]})
    return groups


class DocumentBrowserView(LoginRequiredMixin, View):
    """Read-only, DB-driven aggregation of every uploaded file across the
    app into the fixed folder structure the user asked for - no separate
    file-manager UI, no filesystem scanning. Each file is still owned and
    edited/replaced at its source record (Order, Expense, ...); this page
    is purely "everything in one place to find things again"."""

    template_name = "documents/browser.html"

    def get(self, request):
        bestellungen = self._order_files("etsy_receipt_file")

        ausgangsrechnungen = [
            {"label": f"{i.invoice_number} ({i.date})", "file": i.invoice_file, "date": i.date}
            for i in Income.objects.filter(is_archived=False).exclude(invoice_file="").order_by("-date")
        ]

        eingangsrechnungen = [
            {"label": f"{e.expense_id} ({e.date})", "file": e.invoice_file, "date": e.date}
            for e in Expense.objects.filter(is_archived=False).exclude(invoice_file="").order_by("-date")
        ]

        ust_berichte = [
            {"label": f"{t.get_period_display() or '?'} {t.year}", "file": t.file, "date": t.uploaded_at, "year": t.year}
            for t in TaxReport.objects.all()
        ]

        license_docs_by_type = {}
        for doc in PackagingLicenseDocument.objects.all():
            license_docs_by_type.setdefault(doc.get_doc_type_display(), []).append(
                {"label": f"{doc.year}", "file": doc.file, "date": doc.uploaded_at, "year": doc.year}
            )

        folders = [
            {
                # Kein eigenes Jahresfeld am Beleg selbst - das Jahr wird aus
                # dem Verkaufsdatum der zugehoerigen Bestellung abgeleitet
                # (siehe _order_files/_group_by_year's default year_of).
                "name": "Bestellungen", "icon": "bi-cart3",
                "year_groups": _group_by_year(bestellungen),
            },
            {
                "name": "Finanzen", "icon": "bi-cash-coin",
                "subfolders": [
                    {"name": "Eingangsrechnungen", "year_groups": _group_by_year(eingangsrechnungen)},
                    {"name": "Ausgangsrechnungen", "year_groups": _group_by_year(ausgangsrechnungen)},
                    {"name": "USt-Berichte", "year_groups": _group_by_year(ust_berichte, year_of=lambda e: e["year"])},
                ],
            },
            {
                "name": "Verpackungslizenz", "icon": "bi-recycle",
                "subfolders": [
                    {"name": label, "year_groups": _group_by_year(entries, year_of=lambda e: e["year"])}
                    for label, entries in license_docs_by_type.items()
                ],
            },
        ]

        return render(request, self.template_name, {"folders": folders})

    def _order_files(self, field_name):
        entries = []
        for o in Order.objects.filter(is_archived=False).exclude(**{field_name: ""}).order_by("-sale_date"):
            file = getattr(o, field_name)
            if file:
                entries.append({"label": f"Bestellung #{o.order_id}", "file": file, "date": o.sale_date})
        return entries
