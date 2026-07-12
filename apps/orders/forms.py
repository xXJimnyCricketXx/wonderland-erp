from django import forms
from django.forms import inlineformset_factory

from catalog.models import Article
from contacts.models import Customer
from core.models import ReferenceOption
from knowledge.models import PackagingType

from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "order_id", "etsy_order_number", "customer", "sale_date", "status", "order_type",
            "payment_method", "payment_type", "buyer_username", "number_of_items",
            "date_shipped", "shipping_carrier", "tracking_number", "package_type",
            "ship_street1", "ship_street2", "ship_city", "ship_state", "ship_zipcode", "ship_country",
            "currency", "order_value", "coupon_code", "coupon_details",
            "discount_amount", "shipping_discount", "shipping", "sales_tax", "order_total",
            "card_processing_fees", "order_net",
            "adjusted_order_total", "adjusted_card_processing_fees", "adjusted_net_order_amount",
            "inperson_discount", "inperson_location",
            "etsy_receipt_file",
        ]
        widgets = {
            "order_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "z.B. B-0001"}),
            "etsy_order_number": forms.TextInput(attrs={"class": "form-control"}),
            # HTML5 <input type="date"> requires the value attribute in ISO
            # format - Django's default DateInput renders it in the active
            # locale's format (dd.mm.yyyy for de-de), which the browser then
            # silently fails to parse, showing the field as empty on edit.
            "sale_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "buyer_username": forms.TextInput(attrs={"class": "form-control"}),
            "number_of_items": forms.NumberInput(attrs={"class": "form-control"}),

            "date_shipped": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "shipping_carrier": forms.TextInput(attrs={"class": "form-control"}),
            "tracking_number": forms.TextInput(attrs={"class": "form-control"}),
            "ship_street1": forms.TextInput(attrs={"class": "form-control"}),
            "ship_street2": forms.TextInput(attrs={"class": "form-control"}),
            "ship_city": forms.TextInput(attrs={"class": "form-control"}),
            "ship_state": forms.TextInput(attrs={"class": "form-control"}),
            "ship_zipcode": forms.TextInput(attrs={"class": "form-control"}),
            "ship_country": forms.TextInput(attrs={"class": "form-control"}),

            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "order_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "coupon_code": forms.TextInput(attrs={"class": "form-control"}),
            "coupon_details": forms.TextInput(attrs={"class": "form-control"}),
            "discount_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "shipping_discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "shipping": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "sales_tax": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "order_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "card_processing_fees": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "order_net": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "adjusted_order_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "adjusted_card_processing_fees": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "adjusted_net_order_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "inperson_discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "inperson_location": forms.TextInput(attrs={"class": "form-control"}),
            "etsy_receipt_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(is_archived=False).order_by("last_name", "first_name")
        self.fields["customer"].widget.attrs.update({"class": "form-select"})
        self.fields["package_type"].queryset = PackagingType.objects.all().order_by("name")
        self.fields["package_type"].widget.attrs.update({"class": "form-select"})

        # Status/Bestellart/Zahlungsmethode/Zahlungsart are plain CharFields on
        # the model (Etsy exports free text here), but the options shown to
        # pick from come from the Referenzdaten table, same as Artikel-Kategorie.
        for field_name, category, label in [
            ("status", "order_status", "Status"),
            ("order_type", "order_type", "Bestellart"),
            ("payment_method", "payment_method", "Zahlungsmethode"),
            ("payment_type", "payment_type", "Zahlungsart"),
        ]:
            choices = [("", "---")] + [
                (opt.value, opt.value)
                for opt in ReferenceOption.objects.filter(category=category).order_by("order", "value")
            ]
            self.fields[field_name] = forms.ChoiceField(
                choices=choices,
                required=False,
                label=label,
                widget=forms.Select(attrs={"class": "form-select"}),
            )


class OrderItemForm(forms.ModelForm):
    """sku_raw is deliberately not a form field here - it's Etsy's raw,
    historically-unreliable import value (see OrderItem.sku_raw's comment),
    kept only in the database for reference. The one SKU the user actually
    sees is the assigned article's own SKU, shown read-only once "article"
    is set - having a second editable SKU box next to it was confusing."""

    class Meta:
        model = OrderItem
        fields = ["article", "position"]
        widgets = {
            "article": forms.Select(attrs={"class": "form-select"}),
            "position": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["article"].queryset = Article.objects.filter(is_archived=False).order_by("title")
        self.fields["article"].required = False


OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm, extra=0, can_delete=True,
)
