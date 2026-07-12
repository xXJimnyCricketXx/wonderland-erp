from datetime import date
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect
from lexikon.models import Gemstone
from orders.models import Order

from .forms import (
    CustomsTariffCodeForm, PackagingLicenseDataReportForm, PackagingLicenseDocumentForm, ShippingOptionForm,
)
from .models import (
    CustomsTariffCode, MaterialCategory, PackagingLicenseDataReport, PackagingLicenseDocument,
    PackagingLicenseSubmission, PackagingType, ShippingOption,
)

TABS = ["verpackungslizenz", "versand", "zoll", "preisrechner", "heilsteine"]


def _verpackungslizenz_url(request):
    """Redirect target for any Verpackungslizenz save/delete action - keeps
    the LUCID/Grüne-Punkt pill the user was on. That pill is pure
    client-side Bootstrap state with no query param of its own, so relying
    on the Referer header alone isn't reliable here - the trigger elements
    instead pass `?pill=lucid`/`?pill=gp` explicitly (same explicit
    query-param-propagation pattern as appointments._return_url), which
    survives into POST because the form/button URLs use the full path
    (with query string), not just the bare path."""
    pill = request.GET.get("pill")
    url = reverse("knowledge:infothek") + "?tab=verpackungslizenz"
    if pill in ("lucid", "gp"):
        url += f"&pill={pill}"
    return url


class InfothekView(LoginRequiredMixin, View):
    template_name = "knowledge/infothek.html"

    def get(self, request):
        tab = request.GET.get("tab")
        if tab not in TABS:
            tab = TABS[0]

        context = {"active_tab": tab}
        if tab == "verpackungslizenz":
            context.update(self._verpackungslizenz_context(request))
        elif tab == "versand":
            context.update(self._versand_context())
        elif tab == "zoll":
            context.update(self._zoll_context(request))
        elif tab == "heilsteine":
            context.update(self._heilsteine_context(request))

        return render(request, self.template_name, context)

    def _verpackungslizenz_context(self, request):
        # All order years, not just ones with a package_type already filled
        # in - otherwise a year with zero "Versendet als" entries so far
        # (e.g. older imports where this is still pending) can never be
        # selected to work on in the first place.
        years = list(
            Order.objects.filter(is_archived=False)
            .dates("sale_date", "year", order="DESC")
        )
        year_list = [d.year for d in years]

        try:
            selected_year = int(request.GET.get("jahr", ""))
        except ValueError:
            selected_year = None
        if selected_year not in year_list:
            selected_year = year_list[0] if year_list else date.today().year

        counts = (
            Order.objects.filter(
                is_archived=False, package_type__isnull=False, sale_date__year=selected_year
            )
            .values("package_type")
            .annotate(count=Count("id"))
        )

        categories = list(MaterialCategory.objects.all().order_by("name"))
        totals_kg = [Decimal("0")] * len(categories)
        rows = []
        for entry in counts:
            packaging_type = PackagingType.objects.get(pk=entry["package_type"])
            count = entry["count"]
            kg_by_category_id = {m.material_category_id: m.kg_per_unit for m in packaging_type.materials.all()}
            cells = []
            row_cost = Decimal("0")
            for i, cat in enumerate(categories):
                kg = kg_by_category_id.get(cat.pk, Decimal("0")) * count
                cells.append(kg)
                totals_kg[i] += kg
                row_cost += kg * cat.price_per_kg
            rows.append({"packaging_type": packaging_type, "count": count, "cells": cells, "cost": row_cost})
        rows.sort(key=lambda r: r["packaging_type"].name)

        total_cost = sum((kg * cat.price_per_kg for kg, cat in zip(totals_kg, categories)), Decimal("0"))

        # Ensure the three recurring deadlines exist for EVERY order year,
        # not just whichever one happens to be selected in the Rechner
        # dropdown - otherwise years nobody has browsed to yet (e.g. 2023,
        # 2024) silently never get a Meldungsfristen row at all.
        for y in year_list:
            PackagingLicenseSubmission.objects.get_or_create(
                year=y, submission_type=PackagingLicenseSubmission.TYPE_JAHRESABSCHLUSSMELDUNG
            )
            PackagingLicenseSubmission.objects.get_or_create(
                year=y, submission_type=PackagingLicenseSubmission.TYPE_PLANMENGENANPASSUNG
            )
            PackagingLicenseSubmission.objects.get_or_create(
                year=y, submission_type=PackagingLicenseSubmission.TYPE_LUCID_MELDUNG
            )

        gp_types = [
            PackagingLicenseSubmission.TYPE_JAHRESABSCHLUSSMELDUNG,
            PackagingLicenseSubmission.TYPE_PLANMENGENANPASSUNG,
        ]

        all_reports = PackagingLicenseDataReport.objects.all()
        nachtrag_q = Q(report_type__in=PackagingLicenseDataReport.NACHTRAG_TYPES)

        return {
            "years": year_list,
            "selected_year": selected_year,
            "categories": categories,
            "rows": rows,
            "totals_kg": totals_kg,
            "total_cost": total_cost,
            "license_documents": PackagingLicenseDocument.objects.all(),
            "gp_submissions": PackagingLicenseSubmission.objects.filter(submission_type__in=gp_types),
            "lucid_submissions": PackagingLicenseSubmission.objects.filter(
                submission_type=PackagingLicenseSubmission.TYPE_LUCID_MELDUNG
            ),
            "gp_reports": all_reports.filter(
                recipient=PackagingLicenseDataReport.RECIPIENT_GRUENER_PUNKT
            ).exclude(nachtrag_q),
            "gp_nachtrag_reports": all_reports.filter(
                recipient=PackagingLicenseDataReport.RECIPIENT_GRUENER_PUNKT
            ).filter(nachtrag_q),
            "lucid_reports": all_reports.filter(
                recipient=PackagingLicenseDataReport.RECIPIENT_LUCID
            ).exclude(nachtrag_q),
            "lucid_nachtrag_reports": all_reports.filter(
                recipient=PackagingLicenseDataReport.RECIPIENT_LUCID
            ).filter(nachtrag_q),
        }

    def _versand_context(self):
        return {"shipping_options": ShippingOption.objects.all()}

    def _zoll_context(self, request):
        query = request.GET.get("q", "")
        qs = CustomsTariffCode.objects.all()
        if query:
            qs = qs.filter(
                Q(code__icontains=query) | Q(definition__icontains=query) | Q(description__icontains=query)
            )
        return {"tariff_codes": qs, "query": query}

    def _heilsteine_context(self, request):
        query = request.GET.get("q", "")
        qs = Gemstone.objects.all()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(application__icontains=query))
        return {"gemstones": qs, "query": query}


class ShippingOptionModalMixin(LoginRequiredMixin):
    model = ShippingOption
    form_class = ShippingOptionForm
    template_name = "knowledge/_shipping_option_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("knowledge:infothek") + "?tab=versand")


class ShippingOptionCreateView(ShippingOptionModalMixin, CreateView):
    pass


class ShippingOptionUpdateView(ShippingOptionModalMixin, UpdateView):
    pass


class ShippingOptionDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = ShippingOption

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, reverse("knowledge:infothek") + "?tab=versand")


class TariffCodeModalMixin(LoginRequiredMixin):
    model = CustomsTariffCode
    form_class = CustomsTariffCodeForm
    template_name = "knowledge/_tariff_code_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("knowledge:infothek") + "?tab=zoll")


class TariffCodeCreateView(TariffCodeModalMixin, CreateView):
    pass


class TariffCodeUpdateView(TariffCodeModalMixin, UpdateView):
    pass


class TariffCodeDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = CustomsTariffCode

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, reverse("knowledge:infothek") + "?tab=zoll")


class PackagingLicenseDocumentCreateView(LoginRequiredMixin, CreateView):
    model = PackagingLicenseDocument
    form_class = PackagingLicenseDocumentForm
    template_name = "knowledge/_packaging_license_document_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("knowledge:infothek") + f"?tab=verpackungslizenz&jahr={self.object.year}")


class PackagingLicenseDataReportCreateView(LoginRequiredMixin, CreateView):
    model = PackagingLicenseDataReport
    form_class = PackagingLicenseDataReportForm
    template_name = "knowledge/_packaging_license_data_report_modal.html"

    def get_initial(self):
        initial = super().get_initial()
        recipient_slug = self.request.GET.get("empfaenger")
        if recipient_slug == "lucid":
            initial["recipient"] = PackagingLicenseDataReport.RECIPIENT_LUCID
        elif recipient_slug == "gp":
            initial["recipient"] = PackagingLicenseDataReport.RECIPIENT_GRUENER_PUNKT
        if self.request.GET.get("nachtrag") == "1":
            initial["report_type"] = PackagingLicenseDataReport.TYPE_NACHTRAG
        return initial

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, _verpackungslizenz_url(self.request))


class PackagingLicenseDocumentDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = PackagingLicenseDocument

    def post(self, request, *args, **kwargs):
        year = self.get_object().year
        self.get_object().delete()
        return htmx_redirect(request, reverse("knowledge:infothek") + f"?tab=verpackungslizenz&jahr={year}")


class PackagingLicenseDataReportDetailModalView(LoginRequiredMixin, DetailView):
    model = PackagingLicenseDataReport
    template_name = "knowledge/_packaging_license_data_report_detail_modal.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        materials_by_category = {m.material_category_id: m for m in self.object.materials.all()}
        context["material_rows"] = [
            (cat, materials_by_category.get(cat.pk))
            for cat in MaterialCategory.objects.all().order_by("name")
        ]
        return context


class PackagingLicenseDataReportDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = PackagingLicenseDataReport

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, _verpackungslizenz_url(request))


class PackagingLicenseSubmissionConfirmView(LoginRequiredMixin, SingleObjectMixin, View):
    """Marks a Meldungsfrist as submitted from the navbar bell modal - same
    "dismiss = handled" pattern as appointments.ReminderDismissView, so the
    toast disappears the moment the notification is acted on."""

    model = PackagingLicenseSubmission

    def post(self, request, *args, **kwargs):
        from core.notifications import get_all_notifications

        submission = self.get_object()
        submission.submitted = True
        submission.save(update_fields=["submitted"])

        count = len(get_all_notifications(request))
        html = render_to_string("core/_notification_badge_oob.html", {"count": count})
        return HttpResponse(html)


class PackagingLicenseSubmissionToggleView(LoginRequiredMixin, SingleObjectMixin, View):
    """Plain checkbox-style toggle from the Infothek tab itself (as opposed
    to PackagingLicenseSubmissionConfirmView, which is the bell-notification
    dismiss action and always sets submitted=True)."""

    model = PackagingLicenseSubmission

    def post(self, request, *args, **kwargs):
        submission = self.get_object()
        submission.submitted = not submission.submitted
        submission.save(update_fields=["submitted"])
        pill = "lucid" if submission.submission_type == PackagingLicenseSubmission.TYPE_LUCID_MELDUNG else "gp"
        return htmx_redirect(request, reverse("knowledge:infothek") + f"?tab=verpackungslizenz&pill={pill}")


