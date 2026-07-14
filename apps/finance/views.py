import json
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from contacts.models import Supplier
from core.htmx_utils import htmx_redirect
from core.models import ReferenceOption

from orders.models import Order

from .forms import ExpenseForm, IncomeForm, TaxReportForm
from .models import AccountMapping, Expense, Income, LedgerEntry, SKR03Account, TaxReport

TABS = ["einnahmen", "ausgaben", "rohdaten", "ustberichte", "skr03"]

MONTH_CHOICES = [
    (1, "Januar"), (2, "Februar"), (3, "März"), (4, "April"),
    (5, "Mai"), (6, "Juni"), (7, "Juli"), (8, "August"),
    (9, "September"), (10, "Oktober"), (11, "November"), (12, "Dezember"),
]


class FinanceView(LoginRequiredMixin, View):
    """One page, five tabs (Einnahmen/Ausgaben/Etsy-Rohdaten/USt-Berichte/
    SKR03-Übersicht) - real ?tab= links (full navigation), not client-side
    pills, same reasoning as Kontakte's Kunden/Lieferanten split: each tab
    gets its own independent list."""

    template_name = "finance/finanzen.html"

    def get(self, request):
        tab = request.GET.get("tab")
        tab = tab if tab in TABS else "einnahmen"
        context = {
            "einnahmen": self._income_context,
            "ausgaben": self._expense_context,
            "rohdaten": self._ledger_context,
            "ustberichte": self._tax_report_context,
            "skr03": self._skr03_context,
        }[tab]()
        context["active_tab"] = tab
        return render(request, self.template_name, context)

    def _income_context(self):
        qs = Income.objects.filter(is_archived=False).select_related("order", "customer")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(invoice_number__icontains=query)
                | Q(order__order_id__icontains=query)
                | Q(customer__first_name__icontains=query)
                | Q(customer__last_name__icontains=query)
            )

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return {
            "incomes": qs,
            "query": query or "",
            "selected_category": category or "",
            "selected_status": status or "",
            # Aus Referenzdaten, nicht aus den vorhandenen Einnahmen abgeleitet -
            # sonst fehlen konfigurierte Werte im Filter, solange noch keine
            # Einnahme diese Kategorie/diesen Status trägt.
            "income_categories": ReferenceOption.objects.filter(category="income_category").order_by("order", "value"),
            "income_statuses": ReferenceOption.objects.filter(category="income_status").order_by("order", "value"),
        }

    def _expense_context(self):
        qs = Expense.objects.filter(is_archived=False).select_related("supplier")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(expense_id__icontains=query)
                | Q(invoice_number__icontains=query)
                | Q(description__icontains=query)
                | Q(supplier__first_name__icontains=query)
                | Q(supplier__last_name__icontains=query)
                | Q(supplier__company_name__icontains=query)
            )

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        variant = self.request.GET.get("variant")
        if variant:
            qs = qs.filter(variant=variant)

        supplier = self.request.GET.get("supplier")
        if supplier:
            qs = qs.filter(supplier_id=supplier)

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        base_qs = Expense.objects.filter(is_archived=False)
        return {
            "expenses": qs,
            "query": query or "",
            "selected_category": category or "",
            "selected_variant": variant or "",
            "selected_supplier": supplier or "",
            "selected_supplier_obj": Supplier.objects.filter(pk=supplier).first() if supplier else None,
            "selected_status": status or "",
            # Aus Referenzdaten bzw. der Konten-Zuordnung, nicht aus den
            # vorhandenen Ausgaben abgeleitet - sonst fehlen konfigurierte
            # Werte im Filter, solange noch keine Ausgabe sie trägt.
            "expense_categories": ReferenceOption.objects.filter(category="expense_category").order_by("order", "value"),
            "expense_variants": AccountMapping.objects.exclude(variante="").order_by("variante").values_list("variante", flat=True).distinct(),
            "expense_suppliers": Supplier.objects.filter(pk__in=base_qs.exclude(supplier__isnull=True).values_list("supplier_id", flat=True)).order_by("last_name", "first_name", "company_name"),
            "expense_statuses": ReferenceOption.objects.filter(category="expense_status").order_by("order", "value"),
        }

    def _ledger_context(self):
        qs = LedgerEntry.objects.select_related("order").all()

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(info__icontains=query)
                | Q(order__order_id__icontains=query)
            )

        entry_type = self.request.GET.get("entry_type")
        if entry_type:
            qs = qs.filter(entry_type=entry_type)

        year = self.request.GET.get("year")
        if year:
            qs = qs.filter(date__year=year)

        month = self.request.GET.get("month")
        if month:
            qs = qs.filter(date__month=month)

        return {
            "ledger_entries": qs,
            "query": query or "",
            "selected_entry_type": entry_type or "",
            "selected_year": year or "",
            "selected_month": month or "",
            "selected_month_label": dict(MONTH_CHOICES).get(int(month), "") if month else "",
            # Freitext-Import-Feld (siehe LedgerEntry.entry_type - Etsy kann
            # jederzeit neue Typen einführen), daher Filter aus tatsächlich
            # vorhandenen Werten statt einer festen Referenzdaten-Liste.
            "ledger_entry_types": LedgerEntry.objects.exclude(entry_type="").order_by("entry_type").values_list("entry_type", flat=True).distinct(),
            "ledger_years": [d.year for d in LedgerEntry.objects.dates("date", "year", order="DESC")],
            "ledger_months": MONTH_CHOICES,
        }

    def _tax_report_context(self):
        return {"tax_reports": TaxReport.objects.all()}

    def _skr03_context(self):
        """Pivot: eine Zeile je Ausgabe (ID/Datum/Lieferant), eine Spalte je
        tatsächlich genutztem SKR03-Konto - die Kontobelastung landet in
        genau der Spalte, die zur aufgelösten Art/Variante passt, alle
        anderen Spalten dieser Zeile bleiben leer. Nur Konten, die mindestens
        einer Ausgabe zugeordnet sind, werden als Spalte angezeigt."""
        expenses = list(
            Expense.objects.filter(is_archived=False)
            .select_related("supplier")
            .order_by("date", "expense_id")
        )
        used_account_pks = {expense.skr03_account.pk for expense in expenses if expense.skr03_account}
        columns = list(SKR03Account.objects.filter(pk__in=used_account_pks).order_by("number"))

        totals = [Decimal("0") for _ in columns]
        rows = []
        for expense in expenses:
            account = expense.skr03_account
            amount = expense.account_debit_display
            cells = []
            for i, column in enumerate(columns):
                if account and account.pk == column.pk:
                    cells.append(amount)
                    if amount is not None:
                        totals[i] += amount
                else:
                    cells.append(None)
            rows.append({"expense": expense, "cells": cells})

        return {"skr03_columns": columns, "skr03_rows": rows, "skr03_totals": totals}


class IncomeModalMixin(LoginRequiredMixin):
    model = Income
    form_class = IncomeForm
    template_name = "finance/_income_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # order id -> customer id - lets the modal's JS auto-fill Kunde as
        # soon as eine Bestellung gewählt wird, ohne Server-Roundtrip.
        context["order_customer_json"] = json.dumps(
            {str(pk): customer_id for pk, customer_id in Order.objects.values_list("pk", "customer_id")}
        )
        return context

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("finance:index") + "?tab=einnahmen")


class IncomeCreateView(IncomeModalMixin, CreateView):
    pass


class IncomeUpdateView(IncomeModalMixin, UpdateView):
    pass


class IncomeDetailModalView(LoginRequiredMixin, DetailView):
    model = Income
    template_name = "finance/_income_detail_modal.html"
    context_object_name = "income"


class IncomeArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Income

    def post(self, request, *args, **kwargs):
        self.get_object().archive()
        return htmx_redirect(request, reverse("finance:index") + "?tab=einnahmen")


class ExpenseDetailModalView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = "finance/_expense_detail_modal.html"
    context_object_name = "expense"


class ExpenseModalMixin(LoginRequiredMixin):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/_expense_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # art -> variante -> {nr, name} - lets the modal's JS resolve
        # SKR03-Nr./SKR03-Konto live as Art/Variante are picked, without a
        # round-trip; same source AccountMapping the server-side property uses.
        mapping = {}
        for m in AccountMapping.objects.select_related("skr03_account"):
            mapping.setdefault(m.art, {})[m.variante] = {
                "nr": m.skr03_account.number if m.skr03_account else "",
                "name": m.skr03_account.name if m.skr03_account else "",
            }
        context["account_mapping_json"] = json.dumps(mapping)
        return context

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("finance:index") + "?tab=ausgaben")


class ExpenseCreateView(ExpenseModalMixin, CreateView):
    pass


class ExpenseUpdateView(ExpenseModalMixin, UpdateView):
    pass


class ExpenseArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Expense

    def post(self, request, *args, **kwargs):
        self.get_object().archive()
        return htmx_redirect(request, reverse("finance:index") + "?tab=ausgaben")


class TaxReportModalMixin(LoginRequiredMixin):
    model = TaxReport
    form_class = TaxReportForm
    template_name = "finance/_tax_report_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("finance:index") + "?tab=ustberichte")


class TaxReportCreateView(TaxReportModalMixin, CreateView):
    pass


class TaxReportUpdateView(TaxReportModalMixin, UpdateView):
    pass


class TaxReportDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = TaxReport

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, reverse("finance:index") + "?tab=ustberichte")
