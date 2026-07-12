from django import forms

from core.models import ReferenceOption

from .models import (
    CustomsTariffCode, MaterialCategory, PackagingLicenseDataReport, PackagingLicenseDataReportMaterial,
    PackagingLicenseDocument, ShippingOption,
)


class ShippingOptionForm(forms.ModelForm):
    class Meta:
        model = ShippingOption
        fields = [
            "carrier", "description", "use_case", "price_note",
            "payment_method", "requires_tracking_number", "is_international", "valid_from",
        ]
        widgets = {
            "carrier": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "use_case": forms.TextInput(attrs={"class": "form-control"}),
            "price_note": forms.TextInput(attrs={"class": "form-control"}),
            "requires_tracking_number": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_international": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "valid_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---")] + [
            (opt.value, opt.value)
            for opt in ReferenceOption.objects.filter(category="shipping_payment_method").order_by("order", "value")
        ]
        self.fields["payment_method"] = forms.ChoiceField(
            choices=choices, required=False, label="Bezahlen",
            widget=forms.Select(attrs={"class": "form-select"}),
        )


class CustomsTariffCodeForm(forms.ModelForm):
    class Meta:
        model = CustomsTariffCode
        fields = ["code", "definition", "description"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "definition": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }


class PackagingLicenseDocumentForm(forms.ModelForm):
    class Meta:
        model = PackagingLicenseDocument
        fields = ["year", "doc_type", "file"]
        widgets = {
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "doc_type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class PackagingLicenseDataReportForm(forms.ModelForm):
    """Manual entry for a Datenmeldung - the only option for Der Grüne
    Punkt's older filings, which can only be re-downloaded as PDF, not XML
    (LUCID itself still offers XML re-download, so those can go through the
    Import page instead)."""

    class Meta:
        model = PackagingLicenseDataReport
        fields = [
            "recipient", "report_type", "reporting_period_from", "reporting_period_to",
            "system_operator_id", "source_file",
        ]
        widgets = {
            "recipient": forms.Select(attrs={"class": "form-select"}),
            "report_type": forms.Select(attrs={"class": "form-select"}),
            "reporting_period_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "reporting_period_to": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "system_operator_id": forms.TextInput(attrs={"class": "form-control"}),
            "source_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # One dynamic kg field per MaterialCategory, same pattern as
        # PackagingTypeForm - mirrors the "Mengenangaben" table on the LUCID
        # portal (one column per official material category).
        self.material_categories = MaterialCategory.objects.all().order_by("name")
        existing = {}
        if self.instance.pk:
            existing = {m.material_category_id: m.mass_kg for m in self.instance.materials.all()}
        for cat in self.material_categories:
            self.fields[f"material_{cat.pk}"] = forms.DecimalField(
                label=cat.name, required=False, initial=existing.get(cat.pk, 0),
                max_digits=10, decimal_places=3,
                widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            )

    @property
    def material_fields(self):
        return [(cat, self[f"material_{cat.pk}"]) for cat in self.material_categories]

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self._save_materials(instance)
        return instance

    def _save_materials(self, instance):
        for cat in self.material_categories:
            value = self.cleaned_data.get(f"material_{cat.pk}") or 0
            PackagingLicenseDataReportMaterial.objects.update_or_create(
                report=instance, material_category=cat, defaults={"mass_kg": value},
            )


