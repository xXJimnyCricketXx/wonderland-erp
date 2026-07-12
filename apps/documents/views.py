from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View

from finance.models import Expense
from knowledge.models import PackagingLicenseDocument
from orders.models import Order


class DocumentBrowserView(LoginRequiredMixin, View):
    """Read-only, DB-driven aggregation of every uploaded file across the
    app into the fixed folder structure the user asked for - no separate
    file-manager UI, no filesystem scanning. Each file is still owned and
    edited/replaced at its source record (Order, Expense, ...); this page
    is purely "everything in one place to find things again"."""

    template_name = "documents/browser.html"

    def get(self, request):
        bestellungen = self._order_files("etsy_receipt_file")
        # Einnahmen/Ausgangsrechnungen has no source model/UI yet (Finanzen ->
        # Einnahmen doesn't exist yet, same gap as Ausgaben) - folder stays
        # empty until that module gets built.
        ausgangsrechnungen = []

        eingangsrechnungen = [
            {"label": f"{e.description} ({e.date})", "file": e.invoice_file, "date": e.date}
            for e in Expense.objects.filter(is_archived=False).exclude(invoice_file="").order_by("-date")
        ]
        eingangsrechnungen += [
            {"label": f"Storno: {e.description} ({e.cancelled_at})", "file": e.cancellation_invoice_file, "date": e.cancelled_at}
            for e in Expense.objects.filter(is_archived=False).exclude(cancellation_invoice_file="").order_by("-date")
        ]

        license_docs_by_type = {}
        for doc in PackagingLicenseDocument.objects.all():
            license_docs_by_type.setdefault(doc.get_doc_type_display(), []).append(
                {"label": f"{doc.year}", "file": doc.file, "date": doc.uploaded_at}
            )

        folders = [
            {
                "name": "Bestellungen", "icon": "bi-cart3",
                "entries": bestellungen,
            },
            {
                "name": "Finanzen", "icon": "bi-cash-coin",
                "subfolders": [
                    {"name": "Eingangsrechnungen", "entries": eingangsrechnungen},
                    {"name": "Ausgangsrechnungen", "entries": ausgangsrechnungen},
                ],
            },
            {
                "name": "Verpackungslizenz", "icon": "bi-recycle",
                "subfolders": [
                    {"name": label, "entries": entries}
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
