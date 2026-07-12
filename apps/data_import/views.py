from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from .article_import import import_articles_from_csv
from .forms import (
    ArticleImportForm, OrderImportForm, OrderItemImportForm, PackagingLicenseXmlImportForm, ReviewImportForm,
)
from .order_import import import_orders_from_csv
from .order_item_import import import_order_items_from_csv
from .packaging_license_import import PackagingLicenseImportError, import_packaging_license_xml
from .review_import import import_reviews_from_json


class ImportView(LoginRequiredMixin, TemplateView):
    template_name = "data_import/import.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["article_import_form"] = ArticleImportForm()
        context["order_import_form"] = OrderImportForm()
        context["order_item_import_form"] = OrderItemImportForm()
        context["review_import_form"] = ReviewImportForm()
        context["packaging_license_xml_import_form"] = PackagingLicenseXmlImportForm()
        return context


class ArticleImportView(LoginRequiredMixin, View):
    def post(self, request):
        form = ArticleImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Bitte eine gültige CSV-Datei auswählen.")
            return redirect(reverse("data_import:index") + "?tab=listings")

        result = import_articles_from_csv(form.cleaned_data["file"])

        summary = (
            f"Artikel-Import: {result.created} neu, {result.updated} aktualisiert, "
            f"{result.variants_created} Varianten neu, {result.variants_updated} Varianten aktualisiert."
        )
        if result.skipped:
            summary += f" {len(result.skipped)} Zeile(n) übersprungen."
        messages.success(request, summary)

        for line_number, reason in result.skipped[:20]:
            messages.warning(request, f"Zeile {line_number}: {reason}")

        return redirect(reverse("data_import:index") + "?tab=listings")


class OrderImportView(LoginRequiredMixin, View):
    def post(self, request):
        form = OrderImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Bitte eine gültige CSV-Datei auswählen.")
            return redirect(reverse("data_import:index") + "?tab=orders")

        result = import_orders_from_csv(form.cleaned_data["file"])

        summary = (
            f"Bestellungen-Import: {result.created} neu, {result.updated} aktualisiert, "
            f"{result.customers_created} Kunden neu angelegt, "
            f"{result.order_ids_assigned} Bestell-ID(s) vergeben."
        )
        if result.skipped:
            summary += f" {len(result.skipped)} Zeile(n) übersprungen."
        messages.success(request, summary)

        for line_number, reason in result.skipped[:20]:
            messages.warning(request, f"Zeile {line_number}: {reason}")

        return redirect(reverse("data_import:index") + "?tab=orders")


class OrderItemImportView(LoginRequiredMixin, View):
    def post(self, request):
        form = OrderItemImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Bitte eine gültige CSV-Datei auswählen.")
            return redirect(reverse("data_import:index") + "?tab=orders")

        result = import_order_items_from_csv(form.cleaned_data["file"])

        summary = (
            f"Positionen-Import: {result.orders_updated} Bestellungen aktualisiert, "
            f"{result.items_created} Positionen, {result.listings_seen} neue Etsy-Listings gesehen."
        )
        if result.skipped:
            summary += f" {len(result.skipped)} übersprungen."
        messages.success(request, summary)

        for line_number, reason in result.skipped[:20]:
            prefix = f"Zeile {line_number}: " if line_number else ""
            messages.warning(request, f"{prefix}{reason}")

        return redirect(reverse("data_import:index") + "?tab=orders")


class ReviewImportView(LoginRequiredMixin, View):
    def post(self, request):
        form = ReviewImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Bitte eine gültige JSON-Datei auswählen.")
            return redirect(reverse("data_import:index") + "?tab=reviews")

        result = import_reviews_from_json(form.cleaned_data["file"])

        summary = f"Bewertungen-Import: {result.created} neu, {result.updated} aktualisiert."
        if result.skipped:
            summary += f" {len(result.skipped)} Eintrag/Einträge übersprungen."
        messages.success(request, summary)

        for index, reason in result.skipped[:20]:
            messages.warning(request, f"Eintrag {index}: {reason}")

        return redirect(reverse("data_import:index") + "?tab=reviews")


class PackagingLicenseXmlImportView(LoginRequiredMixin, View):
    def post(self, request):
        form = PackagingLicenseXmlImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Bitte eine gültige XML-Datei und einen Empfänger auswählen.")
            return redirect(reverse("data_import:index") + "?tab=verpackungslizenz")

        try:
            report, materials_created = import_packaging_license_xml(
                form.cleaned_data["file"], form.cleaned_data["recipient"]
            )
        except PackagingLicenseImportError as exc:
            messages.error(request, f"Import fehlgeschlagen: {exc}")
            return redirect(reverse("data_import:index") + "?tab=verpackungslizenz")

        messages.success(
            request,
            f"Datenmeldung importiert: {report.get_recipient_display()}, "
            f"Zeitraum {report.reporting_period_from:%d.%m.%Y}–{report.reporting_period_to:%d.%m.%Y}, "
            f"{materials_created} Materialzeile(n).",
        )
        return redirect(reverse("data_import:index") + "?tab=verpackungslizenz")
