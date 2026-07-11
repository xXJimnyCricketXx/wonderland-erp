import calendar as pycalendar
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from core.models import ReferenceOption

from .colors import annotate_colors, build_color_map
from .forms import AppointmentForm
from .models import Appointment


def _parse_ref_date(raw):
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return date.today()


def _group_by_day(appointments, days):
    by_day = {d: [] for d in days}
    for appt in appointments:
        for d in days:
            if appt.start_date <= d <= appt.end_date:
                by_day[d].append(appt)
    return by_day


SLOT_MINUTES = 15
SLOTS_PER_HOUR = 60 // SLOT_MINUTES
SLOTS_PER_DAY = 24 * SLOTS_PER_HOUR


def _build_week_table(week_dates, timed_by_day):
    """Places each timed appointment into a real table grid (list of rows,
    each row a list of per-day cells) using rowspan, instead of absolute
    pixel positioning - a cell is either "empty", the "start" of an event
    (rendered with rowspan = its duration in slots), or "covered" by an
    event's rowspan from a row above (and must be omitted from that <tr>'s
    markup entirely, which is how HTML tables express rowspan)."""
    grids = {}
    for d in week_dates:
        grid = [None] * SLOTS_PER_DAY
        for slot_index, span, appt in sorted(timed_by_day[d], key=lambda t: t[0]):
            span = min(span, SLOTS_PER_DAY - slot_index)
            if any(grid[i] is not None for i in range(slot_index, slot_index + span)):
                continue  # overlapping appointment - skip rather than corrupt the grid
            grid[slot_index] = ("start", span, appt)
            for i in range(slot_index + 1, slot_index + span):
                grid[i] = "covered"
        grids[d] = grid

    rows = []
    for slot_index in range(SLOTS_PER_DAY):
        is_hour_start = slot_index % SLOTS_PER_HOUR == 0
        cells = []
        for d in week_dates:
            cell = grids[d][slot_index]
            if cell is None:
                cells.append({"type": "empty"})
            elif cell == "covered":
                cells.append({"type": "covered"})
            else:
                _, span, appt = cell
                cells.append({"type": "event", "span": span, "appt": appt})
        rows.append({
            "is_hour_start": is_hour_start,
            "is_half_hour": slot_index % SLOTS_PER_HOUR == SLOTS_PER_HOUR // 2,
            "hour_label": f"{slot_index // SLOTS_PER_HOUR:02d}:00" if is_hour_start else None,
            "cells": cells,
        })
    return rows


def _slot_for_appt(appt):
    start_minutes = appt.start_time.hour * 60 + appt.start_time.minute
    slot_index = start_minutes // SLOT_MINUTES
    if appt.end_time:
        end_minutes = appt.end_time.hour * 60 + appt.end_time.minute
        duration = max(end_minutes - start_minutes, SLOT_MINUTES)
    else:
        # No end time given - show a single minimal slot rather than
        # guessing a full hour that was never actually entered.
        duration = SLOT_MINUTES
    span = max(1, round(duration / SLOT_MINUTES))
    return slot_index, span


class CalendarView(LoginRequiredMixin, View):
    template_name = "appointments/calendar.html"

    def get(self, request):
        view_mode = request.GET.get("view", "month")
        if view_mode not in ("month", "week", "list"):
            view_mode = "month"
        ref_date = _parse_ref_date(request.GET.get("date"))

        color_map = build_color_map(
            ReferenceOption.objects.filter(category="appointment_type")
            .order_by("order", "value").values_list("value", flat=True)
        )

        context = {
            "view_mode": view_mode,
            "ref_date": ref_date,
            "ref_date_iso": ref_date.isoformat(),
            "today": date.today(),
        }

        if view_mode == "month":
            context.update(self._month_context(ref_date, color_map))
        elif view_mode == "week":
            context.update(self._week_context(ref_date, color_map))
        else:
            context.update(self._list_context(request, color_map))

        return render(request, self.template_name, context)

    def _month_context(self, ref_date, color_map):
        cal = pycalendar.Calendar(firstweekday=0)
        month_dates = list(cal.itermonthdates(ref_date.year, ref_date.month))
        range_start, range_end = month_dates[0], month_dates[-1]

        appointments = Appointment.objects.filter(
            start_date__lte=range_end, end_date__gte=range_start
        ).select_related("supplier").prefetch_related("customers")
        annotate_colors(appointments, color_map)

        by_day = _group_by_day(appointments, month_dates)
        weeks = [
            [(d, by_day[d]) for d in month_dates[i:i + 7]]
            for i in range(0, len(month_dates), 7)
        ]

        prev_date = (ref_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        days_in_month = pycalendar.monthrange(ref_date.year, ref_date.month)[1]
        next_date = (ref_date.replace(day=days_in_month) + timedelta(days=1))

        return {
            "weeks": weeks,
            "prev_date_iso": prev_date.isoformat(),
            "next_date_iso": next_date.isoformat(),
        }

    def _week_context(self, ref_date, color_map):
        monday = ref_date - timedelta(days=ref_date.weekday())
        week_dates = [monday + timedelta(days=i) for i in range(7)]
        range_start, range_end = week_dates[0], week_dates[-1]

        appointments = Appointment.objects.filter(
            start_date__lte=range_end, end_date__gte=range_start
        ).select_related("supplier").prefetch_related("customers")
        annotate_colors(appointments, color_map)

        by_day = _group_by_day(appointments, week_dates)
        allday_by_day = {d: [] for d in week_dates}
        timed_by_day = {d: [] for d in week_dates}
        for d in week_dates:
            for appt in by_day[d]:
                # Multi-day appointments always render as a top all-day bar,
                # regardless of whether they carry a time - otherwise a
                # 3-day event would only show on one hour slot on each day.
                if appt.is_all_day or appt.start_date != appt.end_date or not appt.start_time:
                    allday_by_day[d].append(appt)
                else:
                    slot_index, span = _slot_for_appt(appt)
                    timed_by_day[d].append((slot_index, span, appt))

        days = [{"date": d, "allday": allday_by_day[d]} for d in week_dates]
        rows = _build_week_table(week_dates, timed_by_day)

        return {
            "days": days,
            "rows": rows,
            "slots_per_hour": SLOTS_PER_HOUR,
            "prev_date_iso": (monday - timedelta(days=7)).isoformat(),
            "next_date_iso": (monday + timedelta(days=7)).isoformat(),
        }

    def _list_context(self, request, color_map):
        qs = Appointment.objects.select_related("supplier").prefetch_related("customers").order_by("start_date", "start_time")
        paginator = Paginator(qs, 30)
        page_obj = paginator.get_page(request.GET.get("page"))
        annotate_colors(page_obj.object_list, color_map)
        return {
            "appointments": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "paginator": page_obj.paginator,
        }


def _return_url(request):
    """The list/month/week/day the user was looking at when they opened the
    create/edit modal, passed through as ?return_view/?return_date on the
    modal's own GET URL - hx-post="{{ request.get_full_path }}" on the form
    (and the same query string appended to the delete button's hx-post) is
    what carries these back through the POST, so the redirect afterwards
    lands back where the user actually was instead of always defaulting to
    the month view."""
    view = request.GET.get("return_view", "month")
    if view not in ("month", "week", "list"):
        view = "month"
    url = reverse("appointments:calendar") + f"?view={view}"
    return_date = request.GET.get("return_date", "")
    if return_date and view != "list":
        url += f"&date={return_date}"
    return url


class AppointmentModalMixin(LoginRequiredMixin):
    model = Appointment
    form_class = AppointmentForm
    template_name = "appointments/_appointment_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = _return_url(self.request)
        return response


class AppointmentCreateView(AppointmentModalMixin, CreateView):
    def get_initial(self):
        initial = super().get_initial()
        d = self.request.GET.get("date")
        if d:
            initial["start_date"] = d
            initial["end_date"] = d
        return initial


class AppointmentUpdateView(AppointmentModalMixin, UpdateView):
    pass


class AppointmentDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Appointment

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        appointment.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = _return_url(request)
        return response


class ReminderDismissView(LoginRequiredMixin, SingleObjectMixin, View):
    """Acknowledges one reminder from the navbar bell modal. Returns just an
    out-of-band swap for the badge count - htmx extracts that from the
    response before doing the main swap on the toast itself (hx-target),
    which is why the toast disappears even though the response body only
    contains the badge fragment."""

    model = Appointment

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()
        appointment.reminder_dismissed = True
        appointment.save(update_fields=["reminder_dismissed"])

        remaining = Appointment.objects.filter(has_reminder=True, reminder_dismissed=False)
        count = sum(1 for appt in remaining if appt.is_reminder_due)

        html = render_to_string("appointments/_reminder_badge_oob.html", {"count": count})
        return HttpResponse(html)
