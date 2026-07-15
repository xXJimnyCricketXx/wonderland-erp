from django import forms

from core.models import ReferenceOption

from .models import AccountMapping, Expense, Income, TaxReport


def _build_reference_choicefield(category, label, required=False):
    choices = [("", "---")] + [
        (opt.value, opt.value)
        for opt in ReferenceOption.objects.filter(category=category).order_by("order", "value")
    ]
    return forms.ChoiceField(
        choices=choices, required=required, label=label,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


def _build_variant_choicefield():
    """Groups Variante choices by Art (one <optgroup> per Art) straight from
    AccountMapping, so the dropdown always reflects whatever's currently
    configured in Referenzdaten - the "Art" select's JS filters down to the
    matching optgroup, see _expense_modal.html."""
    grouped = {}
    for mapping in AccountMapping.objects.order_by("art", "variante"):
        grouped.setdefault(mapping.art, []).append((mapping.variante, mapping.variante))
    choices = [("", "---")] + list(grouped.items())
    return forms.ChoiceField(
        choices=choices, required=False, label="Variante",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_variant"}),
    )


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = [
            "invoice_number", "invoice_date", "invoice_file", "order", "customer",
            "category", "amount", "vat_rate",
            "payment_method", "paid_date", "payment_account", "status", "notes",
        ]
        widgets = {
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "invoice_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "invoice_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "order": forms.Select(attrs={"class": "form-select", "id": "id_order"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vat_rate": forms.Select(attrs={"class": "form-select"}),
            "paid_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"] = _build_reference_choicefield("income_category", "Kategorie", required=True)
        self.fields["payment_method"] = _build_reference_choicefield("income_payment_method", "Zahlungsart")
        self.fields["payment_account"] = _build_reference_choicefield("payment_account", "Zahlungskonto")
        self.fields["status"] = _build_reference_choicefield("income_status", "Status", required=True)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            # Stammdaten
            "invoice_number", "supplier", "category", "variant", "description",
            "is_eu", "is_third_country", "payment_method", "paid_date", "status", "notes",
            "date", "invoice_date", "invoice_file",
            # Betrag & FX
            "amount", "currency", "fx_rate_eur_per_original", "fx_rate_original_per_eur",
            "fx_fee_percent", "fx_fee_fixed_eur",
            # USt-Aufschlüsselung
            "vat_rate", "gross_7", "gross_19", "gross_0",
            # Kontobelastung
            "account_debit_actual_eur",
        ]
        widgets = {
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "is_eu": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_third_country": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "paid_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "invoice_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "invoice_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "fx_rate_eur_per_original": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "fx_rate_original_per_eur": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "fx_fee_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "fx_fee_fixed_eur": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vat_rate": forms.Select(attrs={"class": "form-select"}),
            "gross_7": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "gross_19": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "gross_0": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "account_debit_actual_eur": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"] = _build_reference_choicefield("expense_category", "Art", required=True)
        self.fields["variant"] = _build_variant_choicefield()
        self.fields["payment_method"] = _build_reference_choicefield("expense_payment_method", "Zahlungsart")
        self.fields["status"] = _build_reference_choicefield("expense_status", "Status", required=True)


class TaxReportForm(forms.ModelForm):
    # Ueberschreibt das Model-Feld (dort null=True/blank=True wegen alter
    # Freitext-Eintraege, die sich nicht automatisch zuordnen lassen) - beim
    # Anlegen/Bearbeiten ueber das Formular ist der Zeitraum aber immer Pflicht.
    period = forms.TypedChoiceField(
        label="Zeitraum", choices=TaxReport._meta.get_field("period").choices,
        coerce=int, required=True, widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = TaxReport
        fields = ["year", "period", "file"]
        widgets = {
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
