from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Sum
from django.shortcuts import render
from django.utils import timezone

from appointments.models import Appointment
from catalog.models import Article
from contacts.models import Customer
from finance.models import Expense, Income
from finance.views import MONTH_CHOICES
from orders.models import Order, OrderItem, Review
from tasks.models import Task

QUARTER_CHOICES = [
    (1, "Q1 (Jan-Mrz)"), (2, "Q2 (Apr-Jun)"), (3, "Q3 (Jul-Sep)"), (4, "Q4 (Okt-Dez)"),
]

MONTH_ABBR = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

# Nur Länder-Zentroide, keine echte Geokodierung - Customer.country ist
# Freitext ohne Koordinaten, daher werden Kunden auf Länderebene als ein
# Bullet je Land gebündelt (Größe = Kundenzahl), nicht als exakter Pin je
# Adresse. Liste deckt die aktuell in den Kundendaten vorkommenden Länder ab.
COUNTRY_CENTROIDS = {
    "Australia": [-25.27, 133.78],
    "Austria": [47.52, 14.55],
    "Denmark": [56.26, 9.50],
    "France": [46.23, 2.21],
    "Germany": [51.17, 10.45],
    "Malaysia": [4.21, 101.98],
    "Singapore": [1.35, 103.82],
    "Spain": [40.46, -3.75],
    "Switzerland": [46.82, 8.23],
    "United Kingdom": [55.38, -3.44],
    "United States": [37.09, -95.71],
}


def _greeting_for_hour(hour, username):
    if 5 <= hour < 11:
        return f"Guten Morgen, {username}!"
    if 11 <= hour < 18:
        return f"Guten Tag, {username}!"
    if 18 <= hour < 22:
        return f"Guten Abend, {username}!"
    # A question, not an exclamation - "Noch so spät wach?" asks, it doesn't state.
    return f"Noch so spät wach, {username}?"


def _parse_int_list(raw):
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


@login_required
def home(request):
    hour = timezone.localtime(timezone.now()).hour

    selected_jahre = _parse_int_list(request.GET.get("jahr", ""))
    selected_monate = _parse_int_list(request.GET.get("monat", ""))

    income_qs = Income.objects.filter(is_archived=False)
    expense_qs = Expense.objects.filter(is_archived=False)
    order_qs = Order.objects.filter(is_archived=False)
    review_qs = Review.objects.all()

    # Keine Auswahl = Gesamtwert über alle Zeit (Standard). Jahr und Monat
    # sind unabhängige Mehrfachauswahlen (Chips), die sich kreuzen - z.B.
    # Jahr 2022+2025 UND Monat Mai+August+Dezember zeigt genau diese
    # Monate in genau diesen Jahren, nicht mehr.
    if selected_jahre:
        income_qs = income_qs.filter(date__year__in=selected_jahre)
        expense_qs = expense_qs.filter(date__year__in=selected_jahre)
        order_qs = order_qs.filter(sale_date__year__in=selected_jahre)
        review_qs = review_qs.filter(date_reviewed__year__in=selected_jahre)
    if selected_monate:
        income_qs = income_qs.filter(date__month__in=selected_monate)
        expense_qs = expense_qs.filter(date__month__in=selected_monate)
        order_qs = order_qs.filter(sale_date__month__in=selected_monate)
        review_qs = review_qs.filter(date_reviewed__month__in=selected_monate)

    avg_rating = review_qs.aggregate(avg=Avg("star_rating"))["avg"]

    income_total = income_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # account_debit_display ist eine Python-@property (Ist, falls erfasst,
    # sonst Soll) - kein DB-Feld, daher hier in Python statt per aggregate() summiert.
    expenses = list(expense_qs)
    expense_total = sum((e.account_debit_display or Decimal("0")) for e in expenses)

    # --- Diagramm-Daten (Chart.js) ---
    # Alle Zeitverlauf-Diagramme teilen dieselbe Monats-Achse (Jan-Dez, oder
    # nur die gewählten Monate) statt einer durchlaufenden Jahr-Monat-Achse -
    # ein Jahr, das mit Januar beginnt, würde sonst optisch mit dem
    # Dezember des Vorjahres verschmelzen. Einnahmen/Ausgaben/Gewinn zeigen
    # deshalb eine eigene Linie je Jahr, genau wie der Vorjahresvergleich.
    available_years = sorted({
        *Income.objects.filter(is_archived=False).exclude(date__isnull=True).values_list("date__year", flat=True),
        *Expense.objects.filter(is_archived=False).exclude(date__isnull=True).values_list("date__year", flat=True),
        *Order.objects.filter(is_archived=False).exclude(sale_date__isnull=True).values_list("sale_date__year", flat=True),
    }, reverse=True)

    years_to_show = sorted(selected_jahre) if selected_jahre else available_years
    months_to_show = sorted(selected_monate) if selected_monate else list(range(1, 13))
    month_axis_labels = [MONTH_ABBR[m - 1] for m in months_to_show]

    # Die Balkendiagramme summieren über mehrere Jahre - ohne Hinweis sieht
    # "Bestellungen pro Monat" bei "Alle Jahre" wie ein einzelnes Jahr aus,
    # zeigt aber z.B. alle Januare 2022-2026 aufaddiert. Diese Caption macht
    # sichtbar, über welche Jahre gerade summiert wird.
    if not years_to_show:
        chart_years_caption = ""
    elif not selected_jahre:
        chart_years_caption = (
            f"Summe {years_to_show[0]}" if len(years_to_show) == 1
            else f"Summe {min(years_to_show)}–{max(years_to_show)}"
        )
    else:
        chart_years_caption = "Summe " + ", ".join(str(y) for y in sorted(years_to_show))

    income_by_year_month = defaultdict(lambda: defaultdict(Decimal))
    for row in income_qs.values("date__year", "date__month").annotate(total=Sum("amount")):
        income_by_year_month[row["date__year"]][row["date__month"]] += row["total"] or Decimal("0")

    expense_by_year_month = defaultdict(lambda: defaultdict(Decimal))
    expense_by_account = defaultdict(Decimal)
    for e in expenses:
        if e.date:
            expense_by_year_month[e.date.year][e.date.month] += e.account_debit_display or Decimal("0")
        account = e.skr03_account
        account_label = f"{account.number} {account.name}" if account else "Ohne Konto"
        expense_by_account[account_label] += e.account_debit_display or Decimal("0")

    order_count_by_year_month = defaultdict(lambda: defaultdict(int))
    for row in order_qs.exclude(sale_date__isnull=True).values("sale_date__year", "sale_date__month").annotate(count=Count("id")):
        order_count_by_year_month[row["sale_date__year"]][row["sale_date__month"]] = row["count"]

    income_series_by_year = {
        str(y): [float(income_by_year_month[y].get(m, Decimal("0"))) for m in months_to_show] for y in years_to_show
    }
    expense_series_by_year = {
        str(y): [float(expense_by_year_month[y].get(m, Decimal("0"))) for m in months_to_show] for y in years_to_show
    }
    profit_series_by_year = {
        str(y): [
            float(income_by_year_month[y].get(m, Decimal("0")) - expense_by_year_month[y].get(m, Decimal("0")))
            for m in months_to_show
        ]
        for y in years_to_show
    }

    # Balkendiagramme (Einnahmen/Ausgaben, Bestellungen) je Monat: über alle
    # gewählten Jahre summiert statt einer Linie je Jahr - ein gruppierter
    # Balken pro Jahr pro Monat wäre bei mehreren Jahren kaum noch lesbar.
    income_bar_series = [sum((income_by_year_month[y].get(m, Decimal("0")) for y in years_to_show), Decimal("0")) for m in months_to_show]
    expense_bar_series = [sum((expense_by_year_month[y].get(m, Decimal("0")) for y in years_to_show), Decimal("0")) for m in months_to_show]
    order_bar_series = [sum(order_count_by_year_month[y].get(m, 0) for y in years_to_show) for m in months_to_show]

    # 3: Ausgaben nach SKR03-Konto, größte Kostenblöcke zuerst.
    skr03_sorted = sorted(expense_by_account.items(), key=lambda item: item[1], reverse=True)
    skr03_labels = [label for label, _total in skr03_sorted]
    skr03_values = [float(total) for _label, total in skr03_sorted]

    # Top 5 Artikel - nach verkauften Einheiten und getrennt nach Einnahmen,
    # jeweils aus den Bestellpositionen der (gefilterten) Bestellungen.
    order_items = OrderItem.objects.filter(order__in=order_qs, article__isnull=False)

    top5_units = list(
        order_items.values("article__title")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )
    top5_units_labels = [row["article__title"] for row in top5_units]
    top5_units_values = [row["total_qty"] or 0 for row in top5_units]

    top5_revenue = list(
        order_items.values("article__title")
        .annotate(total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_revenue")[:5]
    )
    top5_revenue_labels = [row["article__title"] for row in top5_revenue]
    top5_revenue_values = [float(row["total_revenue"] or 0) for row in top5_revenue]

    # Kunden-Karte: Customer.country ist Freitext ohne Koordinaten - eine
    # Geokodierung je Adresse ist außer Scope, daher ein Bullet je Land
    # (Größe = Kundenzahl mit mindestens einer Bestellung im aktuellen Filter).
    customer_ids = order_qs.exclude(customer__isnull=True).values_list("customer_id", flat=True).distinct()
    country_counts = (
        Customer.objects.filter(pk__in=customer_ids)
        .exclude(country="")
        .values("country")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    customer_map_markers = [
        {"name": row["country"], "coords": COUNTRY_CENTROIDS[row["country"]], "count": row["count"]}
        for row in country_counts
        if row["country"] in COUNTRY_CENTROIDS
    ]

    charts_data = {
        "monthAxisLabels": month_axis_labels,
        "incomeSeriesByYear": income_series_by_year,
        "expenseSeriesByYear": expense_series_by_year,
        "profitSeriesByYear": profit_series_by_year,
        "incomeBarSeries": [float(v) for v in income_bar_series],
        "expenseBarSeries": [float(v) for v in expense_bar_series],
        "orderBarSeries": order_bar_series,
        "skr03Labels": skr03_labels,
        "skr03Values": skr03_values,
        "top5UnitsLabels": top5_units_labels,
        "top5UnitsValues": top5_units_values,
        "top5RevenueLabels": top5_revenue_labels,
        "top5RevenueValues": top5_revenue_values,
        "customerMapMarkers": customer_map_markers,
    }

    quarter_active = {}
    for q, _label in QUARTER_CHOICES:
        quarter_months = [(q - 1) * 3 + i for i in (1, 2, 3)]
        quarter_active[q] = bool(selected_monate) and all(m in selected_monate for m in quarter_months)

    open_tasks = Task.objects.filter(is_archived=False).exclude(status="done")
    upcoming_appointments = Appointment.objects.filter(start_date__gte=date.today())

    context = {
        "greeting": _greeting_for_hour(hour, request.user.username),
        "income_total": income_total,
        "expense_total": expense_total,
        "profit_total": income_total - expense_total,
        "article_count": Article.objects.filter(parent_article__isnull=True, is_archived=False).count(),
        "order_count": order_qs.count(),
        "avg_rating": avg_rating,
        "available_years": available_years,
        "months": MONTH_CHOICES,
        "quarters": QUARTER_CHOICES,
        "quarter_active": quarter_active,
        "selected_jahre": selected_jahre,
        "selected_monate": selected_monate,
        "charts_data": charts_data,
        "chart_years_caption": chart_years_caption,
        "open_task_count": open_tasks.count(),
        "open_tasks": open_tasks.order_by(F("due_date").asc(nulls_last=True))[:5],
        "appointment_count": upcoming_appointments.count(),
        "upcoming_appointments": upcoming_appointments.order_by("start_date", "start_time")[:5],
    }
    return render(request, "dashboard/home.html", context)
