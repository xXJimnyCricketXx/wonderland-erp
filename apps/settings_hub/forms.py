from django import forms

from knowledge.models import MaterialCategory, PackagingType, PackagingTypeMaterial

from .models import CompanyProfile


class PackagingTypeForm(forms.ModelForm):
    class Meta:
        model = PackagingType
        fields = ["name", "description", "dimensions", "valid_from"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "dimensions": forms.TextInput(attrs={"class": "form-control", "placeholder": "z.B. 25,0 x 17,5 x 10,0 cm"}),
            "valid_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # One dynamic kg-per-unit field per MaterialCategory, named by pk so
        # the category list can grow without touching this form - mirrors the
        # ReferenceOption-driven ChoiceField pattern used elsewhere.
        self.material_categories = MaterialCategory.objects.all().order_by("name")
        existing = {}
        if self.instance.pk:
            existing = {m.material_category_id: m.kg_per_unit for m in self.instance.materials.all()}
        for cat in self.material_categories:
            self.fields[f"material_{cat.pk}"] = forms.DecimalField(
                label=cat.name, required=False, initial=existing.get(cat.pk, 0),
                max_digits=6, decimal_places=4,
                widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
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
            PackagingTypeMaterial.objects.update_or_create(
                packaging_type=instance, material_category=cat, defaults={"kg_per_unit": value},
            )


class MaterialCategoryForm(forms.ModelForm):
    class Meta:
        model = MaterialCategory
        fields = ["name", "price_per_kg"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price_per_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
        }


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "company_name", "street1", "street2", "zipcode", "city", "country",
            "tax_number", "vat_id", "email", "website",
            "etsy_shop_url", "instagram_url", "facebook_url",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "street1": forms.TextInput(attrs={"class": "form-control"}),
            "street2": forms.TextInput(attrs={"class": "form-control"}),
            "zipcode": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "tax_number": forms.TextInput(attrs={"class": "form-control"}),
            "vat_id": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "etsy_shop_url": forms.URLInput(attrs={"class": "form-control"}),
            "instagram_url": forms.URLInput(attrs={"class": "form-control"}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control"}),
        }
