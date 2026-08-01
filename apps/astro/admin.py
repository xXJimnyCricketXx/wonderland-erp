import base64

from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import ReportBrandingAdminForm, ThemenBildAdminForm, ZodiacSignAdminForm
from .models import (
    BirthChart,
    GemstoneCorrespondence,
    GeneratedReport,
    GeocodeCache,
    HausherrAszendentText,
    House,
    InterpretationText,
    Planet,
    PlanetHouseText,
    ReportBranding,
    ShortDescription,
    SonneAszendentKombiText,
    SonneMondKombiText,
    ThemenBild,
    ZodiacSign,
)
from .services.report_builder import build_chapter_preview_pdf, build_planet_sign_chapter_preview
from .services.text_render import render_body, render_sonne_mond_kombi_html


def _blob_image_preview(data, content_type="image/png", height=80):
    """Die Upload-Felder fuer Blob-Bilder (siehe forms.py) sind reine
    Datei-Auswahl-Widgets ohne Bezug zum bereits gespeicherten Bild - beim
    erneuten Oeffnen wirkt es dadurch immer so, als waere nichts hochgeladen,
    obwohl der Blob laengst in der DB steckt. Diese Vorschau (als readonly
    Feld) zeigt den tatsaechlichen Stand."""
    if not data:
        return "– kein Bild hochgeladen –"
    image_base64 = base64.b64encode(bytes(data)).decode()
    return format_html(
        '<img src="data:{};base64,{}" style="max-height: {}px; background: #eee; padding: 4px;">',
        content_type, image_base64, height,
    )


class BausteinPreviewMixin:
    """Fuegt einen "Vorschau in neuem Tab oeffnen"-Button hinzu (WordPress-
    artig). Die Vorschau ist ein echtes, mit weasyprint gerendertes Mini-PDF
    ueber dieselbe @page-content-page-CSS wie der finale Report (siehe
    chapter_preview.html) - dadurch fallen Seitenumbrueche exakt so wie im
    echten PDF, man sieht also z.B. ob ein Absatz mitten auf der Seite
    umbricht. Zeigt das GANZE Kapitel, in das dieser Baustein gehoert
    (mehrere aneinandergehaengte Bausteine), nicht nur diesen einen Text -
    und dabei auch unveroeffentlichte Entwuerfe, damit man das komplette
    geplante Kapitel pruefen kann. Zeigt immer den zuletzt GESPEICHERTEN
    Stand, kein Live-Preview waehrend des Tippens.
    Erwartet in der Subklasse: preview_chapter_func(obj) -> (heading, html)."""

    readonly_fields = ["preview_button"]
    preview_chapter_func = None

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path(
                "<int:object_id>/vorschau/",
                self.admin_site.admin_view(self.preview_view),
                name="%s_%s_vorschau" % info,
            ),
        ]
        return custom_urls + super().get_urls()

    def preview_view(self, request, object_id):
        obj = get_object_or_404(self.model, pk=object_id)
        heading, content_html = self.preview_chapter_func(obj)
        pdf_bytes = build_chapter_preview_pdf(heading, content_html or "<p><em>– noch kein Inhalt –</em></p>")
        return HttpResponse(pdf_bytes, content_type="application/pdf")

    def preview_button(self, obj):
        if not obj or not obj.pk:
            return "– erst nach dem Speichern verfuegbar –"
        info = self.model._meta.app_label, self.model._meta.model_name
        url = reverse("admin:%s_%s_vorschau" % info, args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">Seitenumbruch-Vorschau (PDF) in neuem Tab oeffnen</a>',
            url,
        )
    preview_button.short_description = "Vorschau"


@admin.register(ZodiacSign)
class ZodiacSignAdmin(admin.ModelAdmin):
    form = ZodiacSignAdminForm
    list_display = ["name_de", "element", "quality", "ruler_planet", "sort_order"]
    ordering = ["sort_order"]
    readonly_fields = [
        "symbol_image_png_preview", "symbol_image_svg_preview",
        "zodiac_image_png_preview", "zodiac_image_svg_preview",
    ]

    def symbol_image_png_preview(self, obj):
        return _blob_image_preview(obj.symbol_image_png if obj else None, "image/png")
    symbol_image_png_preview.short_description = "Aktuelles Symbolbild (PNG)"

    def symbol_image_svg_preview(self, obj):
        return _blob_image_preview(obj.symbol_image_svg if obj else None, "image/svg+xml")
    symbol_image_svg_preview.short_description = "Aktuelles Symbolbild (SVG)"

    def zodiac_image_png_preview(self, obj):
        return _blob_image_preview(obj.zodiac_image_png if obj else None, "image/png")
    zodiac_image_png_preview.short_description = "Aktuelles Zeichenbild (PNG)"

    def zodiac_image_svg_preview(self, obj):
        return _blob_image_preview(obj.zodiac_image_svg if obj else None, "image/svg+xml")
    zodiac_image_svg_preview.short_description = "Aktuelles Zeichenbild (SVG)"


@admin.register(Planet)
class PlanetAdmin(admin.ModelAdmin):
    list_display = ["name_de", "key", "is_angle", "is_optional_body"]


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ["number", "name_de", "short_meaning"]


@admin.register(ShortDescription)
class ShortDescriptionAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["planet", "sign", "status", "author"]
    list_filter = ["status", "planet"]
    search_fields = ["body"]
    preview_chapter_func = staticmethod(lambda obj: build_planet_sign_chapter_preview(obj.planet.key, obj.sign))


@admin.register(InterpretationText)
class InterpretationTextAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["planet", "sign", "text_type", "heading", "status", "author", "reviewed_by"]
    list_filter = ["status", "text_type", "planet"]
    search_fields = ["body", "source_notes", "heading"]
    preview_chapter_func = staticmethod(lambda obj: build_planet_sign_chapter_preview(obj.planet.key, obj.sign))


@admin.register(SonneMondKombiText)
class SonneMondKombiTextAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["sign_sonne", "sign_mond", "status"]
    list_filter = ["status"]
    preview_chapter_func = staticmethod(lambda obj: (
        f"{obj.sign_sonne.name_de} mit Mond in {obj.sign_mond.name_de}",
        render_sonne_mond_kombi_html(obj),
    ))


@admin.register(SonneAszendentKombiText)
class SonneAszendentKombiTextAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["sign_sonne", "sign_aszendent", "status"]
    list_filter = ["status"]
    preview_chapter_func = staticmethod(lambda obj: (
        f"{obj.sign_sonne.name_de} Aszendent {obj.sign_aszendent.name_de}",
        render_body(obj.body),
    ))


@admin.register(HausherrAszendentText)
class HausherrAszendentTextAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["sign_aszendent", "house", "status"]
    list_filter = ["status"]
    preview_chapter_func = staticmethod(lambda obj: (
        f"Aszendent {obj.sign_aszendent.name_de} – Hausherr im {obj.house.number}. Haus",
        render_body(obj.body),
    ))


@admin.register(PlanetHouseText)
class PlanetHouseTextAdmin(BausteinPreviewMixin, admin.ModelAdmin):
    list_display = ["planet", "house", "status"]
    list_filter = ["status", "planet"]
    preview_chapter_func = staticmethod(lambda obj: (
        f"{obj.planet.name_de} im {obj.house.number}. Haus",
        render_body(obj.body),
    ))


@admin.register(ThemenBild)
class ThemenBildAdmin(admin.ModelAdmin):
    form = ThemenBildAdminForm
    list_display = ["topic"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        return _blob_image_preview(obj.image_data if obj else None, obj.content_type if obj else "image/png")
    image_preview.short_description = "Aktuelles Bild"


@admin.register(GemstoneCorrespondence)
class GemstoneCorrespondenceAdmin(admin.ModelAdmin):
    list_display = ["heilstein_ref", "role", "sign", "planet"]
    list_filter = ["role"]
    search_fields = ["heilstein_ref"]


@admin.register(BirthChart)
class BirthChartAdmin(admin.ModelAdmin):
    list_display = ["label", "birth_date", "birth_place_raw", "sun_sign", "moon_sign", "ascendant_sign"]


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ["chart", "format", "order_reference", "generated_at"]
    list_filter = ["format"]


@admin.register(GeocodeCache)
class GeocodeCacheAdmin(admin.ModelAdmin):
    list_display = ["name", "query", "country", "lat", "lon", "timezone"]
    search_fields = ["query", "name"]


@admin.register(ReportBranding)
class ReportBrandingAdmin(admin.ModelAdmin):
    """Singleton - Admin-Liste ueberspringen und direkt zur (einzigen)
    Bearbeiten-Seite springen, "Hinzufuegen" nur anbieten, solange noch
    keine Zeile existiert (siehe ReportBranding.save(), das ohnehin immer
    pk=1 erzwingt)."""

    form = ReportBrandingAdminForm
    list_display = ["content_type"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        return _blob_image_preview(obj.image_data if obj else None, obj.content_type if obj else "image/png")
    image_preview.short_description = "Aktuelles Bild"

    def has_add_permission(self, request):
        return not ReportBranding.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        branding = ReportBranding.objects.first()
        if branding:
            return HttpResponseRedirect(
                reverse("admin:astro_reportbranding_change", args=[branding.pk])
            )
        return HttpResponseRedirect(reverse("admin:astro_reportbranding_add"))
