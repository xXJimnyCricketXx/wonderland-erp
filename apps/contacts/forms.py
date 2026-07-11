from django import forms
from django.forms import inlineformset_factory

from core.models import ReferenceOption

from .models import Customer, Supplier, SupplierDiscountTier

CONTACT_BASE_WIDGETS = {
    "first_name": forms.TextInput(attrs={"class": "form-control"}),
    "last_name": forms.TextInput(attrs={"class": "form-control"}),
    "company_name": forms.TextInput(attrs={"class": "form-control"}),
    "job_title": forms.TextInput(attrs={"class": "form-control"}),
    "street1": forms.TextInput(attrs={"class": "form-control"}),
    "street2": forms.TextInput(attrs={"class": "form-control"}),
    "city": forms.TextInput(attrs={"class": "form-control"}),
    "state": forms.TextInput(attrs={"class": "form-control"}),
    "zipcode": forms.TextInput(attrs={"class": "form-control"}),
    "country": forms.TextInput(attrs={"class": "form-control"}),
    "email": forms.EmailInput(attrs={"class": "form-control"}),
    "phone": forms.TextInput(attrs={"class": "form-control"}),
    "birthday": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
    "last_contact_at": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
    "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
}


def _build_reference_choicefield(category, label, required=False):
    choices = [("", "---")] + [
        (opt.value, opt.value)
        for opt in ReferenceOption.objects.filter(category=category).order_by("order", "value")
    ]
    return forms.ChoiceField(
        choices=choices, required=required, label=label,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "first_name", "last_name", "company_name", "job_title",
            "street1", "street2", "city", "state", "zipcode", "country",
            "email", "phone", "preferred_contact_method",
            "birthday", "last_contact_at", "status", "notes",
            "etsy_buyer_user_id", "is_returning_customer",
        ]
        widgets = {
            **CONTACT_BASE_WIDGETS,
            "etsy_buyer_user_id": forms.TextInput(attrs={"class": "form-control"}),
            "is_returning_customer": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_contact_method"] = _build_reference_choicefield(
            "preferred_contact_method", "Bevorzugte Kontaktart"
        )
        self.fields["status"] = _build_reference_choicefield("contact_status", "Status")


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "first_name", "last_name", "company_name", "job_title",
            "street1", "street2", "city", "state", "zipcode", "country",
            "email", "phone", "preferred_contact_method",
            "birthday", "last_contact_at", "status", "notes",
            "website", "account_number", "payment_terms", "lead_time_days",
            "vat_id", "standard_discount_percent", "platform",
        ]
        widgets = {
            **CONTACT_BASE_WIDGETS,
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "account_number": forms.TextInput(attrs={"class": "form-control"}),
            "payment_terms": forms.TextInput(attrs={"class": "form-control"}),
            "lead_time_days": forms.NumberInput(attrs={"class": "form-control"}),
            "vat_id": forms.TextInput(attrs={"class": "form-control"}),
            "standard_discount_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_contact_method"] = _build_reference_choicefield(
            "preferred_contact_method", "Bevorzugte Kontaktart"
        )
        self.fields["status"] = _build_reference_choicefield("contact_status", "Status")

        platform_qs = Supplier.objects.filter(is_archived=False).order_by("last_name", "first_name")
        if self.instance.pk:
            platform_qs = platform_qs.exclude(pk=self.instance.pk)
        self.fields["platform"].queryset = platform_qs
        self.fields["platform"].widget.attrs.update({"class": "form-select"})


SupplierDiscountTierFormSet = inlineformset_factory(
    Supplier,
    SupplierDiscountTier,
    fields=["min_order_value", "discount_percent"],
    widgets={
        "min_order_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        "discount_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    },
    extra=0,
    can_delete=True,
)
