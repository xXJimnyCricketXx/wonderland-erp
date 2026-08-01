from django import forms
from django.core.exceptions import ValidationError

from .models import BirthChart, ReportBranding, ThemenBild, ZodiacSign


def _validate_svg(uploaded_file):
    if uploaded_file and not uploaded_file.name.lower().endswith(".svg"):
        raise ValidationError("Bitte eine SVG-Datei hochladen.")


class ZodiacSignAdminForm(forms.ModelForm):
    """BinaryField hat kein sinnvolles Standard-Widget - die Bilder werden
    hier als separate Upload-Felder entgegengenommen und in save() auf die
    Blob-Felder geschrieben, gleiches Muster wie Gemstone.image_data im
    Heilstein-Lexikon. SVGs laufen ueber ein einfaches FileField statt
    ImageField, da Djangos ImageField-Validierung (Pillow) keine SVGs lesen
    kann."""

    symbol_image_png_upload = forms.ImageField(label="Symbolbild (PNG)", required=False)
    symbol_image_svg_upload = forms.FileField(label="Symbolbild (SVG)", required=False, validators=[_validate_svg])
    zodiac_image_png_upload = forms.ImageField(label="Zeichenbild (PNG)", required=False)
    zodiac_image_svg_upload = forms.FileField(label="Zeichenbild (SVG)", required=False, validators=[_validate_svg])

    class Meta:
        model = ZodiacSign
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        for upload_field, target_field in [
            ("symbol_image_png_upload", "symbol_image_png"),
            ("symbol_image_svg_upload", "symbol_image_svg"),
            ("zodiac_image_png_upload", "zodiac_image_png"),
            ("zodiac_image_svg_upload", "zodiac_image_svg"),
        ]:
            upload = self.cleaned_data.get(upload_field)
            if upload:
                setattr(instance, target_field, upload.read())
        if commit:
            instance.save()
        return instance


class ThemenBildAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(label="Bild", required=False)

    class Meta:
        model = ThemenBild
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get("image_upload")
        if image:
            instance.image_data = image.read()
            instance.content_type = image.content_type
        if commit:
            instance.save()
        return instance


class ReportBrandingAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(label="Deckblatt-Hintergrund", required=False)

    class Meta:
        model = ReportBranding
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get("image_upload")
        if image:
            instance.image_data = image.read()
            instance.content_type = image.content_type
        if commit:
            instance.save()
        return instance


class BirthChartForm(forms.Form):
    label = forms.CharField(
        label="Bezeichnung", max_length=150, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "z. B. Kundenname"}),
    )
    birth_date = forms.DateField(
        label="Geburtsdatum",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    birth_time = forms.TimeField(
        label="Geburtszeit", required=False,
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        help_text="Leer lassen, falls unbekannt – dann ohne Häuser/Aszendent.",
    )
    birth_place = forms.CharField(
        label="Geburtsort", max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control", "placeholder": "z. B. Bad Kreuznach, Deutschland",
            "autocomplete": "off", "id": "id_birth_place",
        }),
    )
    # Von der Autocomplete-JS befuellt (siehe _birth_chart_modal.html), wenn
    # ein Vorschlag ausgewaehlt wurde - sonst leer, dann greift beim Submit
    # der Text-Fallback (geocode_place) in BirthChartCreateView.
    birth_lat = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={"id": "id_birth_lat"}))
    birth_lon = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={"id": "id_birth_lon"}))
    geonameid = forms.CharField(required=False, widget=forms.HiddenInput(attrs={"id": "id_geonameid"}))
    house_system = forms.ChoiceField(
        label="Häusersystem", choices=BirthChart.HOUSE_SYSTEMS, initial="placidus",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    include_chiron = forms.BooleanField(
        label="Chiron", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    include_pholus = forms.BooleanField(
        label="Pholus", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    include_lilith = forms.BooleanField(
        label="Lilith", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
