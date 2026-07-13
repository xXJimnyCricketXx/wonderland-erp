from datetime import date
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View

from finance.models import Expense, Income
from settings_hub.models import CompanyProfile

PERIOD_TYPES = ["jahr", "halbjahr", "quartal"]


def _effective_date(entry):
    """Zufluss-/Abfluss-Prinzip (§11 EStG) - für die EÜR zählt das
    Zahlungsdatum, nicht das Rechnungs-/Verkaufsdatum. Fällt auf `date`
    zurück, solange kein Zahlungsdatum erfasst ist."""
    return entry.paid_date or entry.date


def _period_matches(entry_date, year, period_type, period_value):
    if entry_date is None or entry_date.year != year:
        return False
    if period_type == "halbjahr" and period_value:
        return (1 if entry_date.month <= 6 else 2) == period_value
    if period_type == "quartal" and period_value:
        return (entry_date.month - 1) // 3 + 1 == period_value
    return True


class ReportsView(LoginRequiredMixin, View):
    template_name = "reports/reports.html"

    def get(self, request):
        incomes_all = list(Income.objects.filter(is_archived=False).select_related("customer", "order"))
        expenses_all = list(Expense.objects.filter(is_archived=False).select_related("supplier"))

        available_years = sorted(
            {_effective_date(i).year for i in incomes_all if _effective_date(i)}
            | {_effective_date(e).year for e in expenses_all if _effective_date(e)},
            reverse=True,
        )

        year = int(request.GET.get("jahr") or (available_years[0] if available_years else date.today().year))
        period_type = request.GET.get("zeitraum") or "jahr"
        if period_type not in PERIOD_TYPES:
            period_type = "jahr"
        period_value_raw = request.GET.get("teilzeitraum")
        period_value = int(period_value_raw) if period_value_raw else None

        income_rows = []
        income_total = Decimal("0")
        for i in incomes_all:
            d = _effective_date(i)
            if _period_matches(d, year, period_type, period_value):
                income_rows.append(i)
                income_total += i.amount
        income_rows.sort(key=_effective_date)

        expense_rows = []
        expense_total = Decimal("0")
        expense_by_account = {}
        for e in expenses_all:
            d = _effective_date(e)
            if _period_matches(d, year, period_type, period_value):
                betrag = e.account_debit_display or Decimal("0")
                expense_rows.append(e)
                expense_total += betrag
                konto = e.skr03_account.name if e.skr03_account else "Unbekannt"
                expense_by_account[konto] = expense_by_account.get(konto, Decimal("0")) + betrag
        expense_rows.sort(key=_effective_date)

        expense_by_account_sorted = sorted(expense_by_account.items(), key=lambda x: x[1], reverse=True)

        context = {
            "company": CompanyProfile.load(),
            "year": year,
            "period_type": period_type,
            "period_value": period_value,
            "available_years": available_years,
            "income_total": income_total,
            "expense_total": expense_total,
            "profit": income_total - expense_total,
            "expense_by_account": expense_by_account_sorted,
            "income_rows": income_rows,
            "expense_rows": expense_rows,
            "today": date.today(),
        }
        return render(request, self.template_name, context)
