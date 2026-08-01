from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect

from .forms import BirthChartForm
from .models import BirthChart, ZodiacSign
from .services.chart_builder import build_birth_chart
from .services.chart_image import render_chart_wheel_svg
from .services.geocode import GeocodeError, resolve_timezone, search_places
from .services.report_builder import build_report_pdf

POINT_ORDER = [
    "sonne", "mond", "merkur", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptun", "pluto", "mondknoten", "lilith", "chiron", "pholus",
]
POINT_LABELS = {
    "sonne": "Sonne", "mond": "Mond", "merkur": "Merkur", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus",
    "neptun": "Neptun", "pluto": "Pluto", "mondknoten": "Mondknoten",
    "chiron": "Chiron", "lilith": "Lilith", "pholus": "Pholus",
}


def _infothek_url():
    return reverse("knowledge:infothek") + "?tab=horoskope"


def _format_degree(longitude):
    deg_in_sign = longitude % 30
    degrees = int(deg_in_sign)
    minutes = int(round((deg_in_sign - degrees) * 60))
    if minutes == 60:
        minutes = 0
        degrees += 1
    return f"{degrees}°{minutes:02d}"


def _submit_birth_chart_form(data, chart=None):
    """Gemeinsame Logik fuer Neuanlage und Bearbeiten: wenn per Autocomplete
    ein Vorschlag gewaehlt wurde, sind Koordinaten schon bekannt - nur noch
    Zeitzone dazu aufloesen (ein API-Call statt zwei). Sonst Text-Fallback
    ueber geocode_place (in build_birth_chart)."""
    kwargs = dict(
        label=data["label"],
        birth_date=data["birth_date"],
        birth_time=data["birth_time"],
        birth_place=data["birth_place"],
        house_system=data["house_system"],
        include_chiron=data["include_chiron"],
        include_pholus=data["include_pholus"],
        include_lilith=data["include_lilith"],
        chart=chart,
    )
    if data["birth_lat"] is not None and data["birth_lon"] is not None:
        kwargs["lat"] = data["birth_lat"]
        kwargs["lon"] = data["birth_lon"]
        kwargs["tz_str"] = resolve_timezone(data["birth_lat"], data["birth_lon"])
        kwargs["geonameid"] = data["geonameid"]
    return build_birth_chart(**kwargs)


class BirthChartGeocodeSuggestView(LoginRequiredMixin, View):
    """Live-Autocomplete waehrend des Tippens im Geburtsort-Feld - siehe
    services/geocode.py:search_places(). Liefert bei jedem Fehler (fehlender
    Account, GeoNames nicht erreichbar) einfach eine leere Liste statt eines
    Fehlercodes, damit die Autocomplete im Formular niemals blockiert; der
    harte Fehler kommt erst beim tatsaechlichen Submit (geocode_place)."""

    def get(self, request):
        query = request.GET.get("q", "")
        try:
            results = search_places(query) if len(query) >= 2 else []
        except Exception:
            results = []
        return JsonResponse({"results": results})


class BirthChartCreateView(LoginRequiredMixin, View):
    template_name = "astro/_birth_chart_modal.html"

    def get(self, request):
        form = BirthChartForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = BirthChartForm(request.POST)
        if form.is_valid():
            try:
                _submit_birth_chart_form(form.cleaned_data)
            except GeocodeError as exc:
                form.add_error("birth_place", str(exc))
                return render(request, self.template_name, {"form": form})
            return htmx_redirect(request, _infothek_url())
        return render(request, self.template_name, {"form": form})


class BirthChartUpdateView(LoginRequiredMixin, SingleObjectMixin, View):
    """Aendert die Eingabedaten eines bestehenden Horoskops und berechnet es
    neu (statt loeschen + neu anlegen) - dieselbe build_birth_chart()-Logik
    wie beim Neuanlegen, nur mit chart=self.object statt einer neuen Zeile."""

    model = BirthChart
    template_name = "astro/_birth_chart_modal.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BirthChartForm(initial={
            "label": self.object.label,
            "birth_date": self.object.birth_date,
            "birth_time": self.object.birth_time,
            "birth_place": self.object.birth_place_raw,
            "birth_lat": self.object.birth_lat,
            "birth_lon": self.object.birth_lon,
            "geonameid": self.object.geonameid,
            "house_system": self.object.house_system,
            "include_chiron": self.object.include_chiron,
            "include_pholus": self.object.include_pholus,
            "include_lilith": self.object.include_lilith,
        })
        return render(request, self.template_name, {"form": form, "object": self.object})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BirthChartForm(request.POST)
        if form.is_valid():
            try:
                _submit_birth_chart_form(form.cleaned_data, chart=self.object)
            except GeocodeError as exc:
                form.add_error("birth_place", str(exc))
                return render(request, self.template_name, {"form": form, "object": self.object})
            return htmx_redirect(request, _infothek_url())
        return render(request, self.template_name, {"form": form, "object": self.object})


class BirthChartDetailModalView(LoginRequiredMixin, SingleObjectMixin, View):
    model = BirthChart
    template_name = "astro/_birth_chart_detail_modal.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        sign_names = dict(ZodiacSign.objects.values_list("key", "name_de"))
        points_raw = (self.object.raw_positions or {}).get("points", {})
        positions = []
        for key in POINT_ORDER:
            point = points_raw.get(key)
            if not point:
                continue
            positions.append({
                "label": POINT_LABELS[key],
                "sign": sign_names.get(point["sign"], point["sign"]),
                "degree": _format_degree(point["longitude"]),
                "house": point.get("house"),
                "retrograde": point.get("retrograde", False),
            })

        # Aszendent = Spitze des 1. Hauses, MC = Spitze des 10. Hauses - beide
        # stecken schon in house_cusps (siehe ephemeris.py), keine eigene
        # Laenge noetig.
        house_cusps = (self.object.raw_positions or {}).get("house_cusps") or []
        ascendant_degree = _format_degree(house_cusps[0]) if house_cusps else None
        mc_degree = _format_degree(house_cusps[9]) if house_cusps else None

        chart_svg = None
        if self.object.birth_time:
            try:
                chart_svg = render_chart_wheel_svg(
                    birth_date=self.object.birth_date, birth_time=self.object.birth_time,
                    lat=self.object.birth_lat, lon=self.object.birth_lon,
                    tz_str=self.object.birth_timezone, house_system=self.object.house_system,
                    city=self.object.birth_place_raw,
                    name=self.object.label or "Horoskop",
                )
            except Exception:
                chart_svg = None

        return render(request, self.template_name, {
            "chart": self.object,
            "positions": positions,
            "ascendant_degree": ascendant_degree,
            "mc_degree": mc_degree,
            "chart_svg": chart_svg,
        })


class BirthChartDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = BirthChart

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, _infothek_url())


class BirthChartReportView(LoginRequiredMixin, SingleObjectMixin, View):
    """Erzeugt den PDF-Bericht bei jedem Aufruf frisch (noch keine
    gespeicherte GeneratedReport-Historie - sinnvoll erst, wenn die
    Textinhalte redaktionell fertig sind) und zeigt ihn direkt im Browser an."""

    model = BirthChart

    def get(self, request, *args, **kwargs):
        chart = self.get_object()
        pdf_bytes = build_report_pdf(chart)
        filename = f"Geburtshoroskop_{chart.label or chart.pk}.pdf".replace(" ", "_")
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response
