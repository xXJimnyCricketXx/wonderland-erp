from django import forms

from .models import ShoppingListItem


class ShoppingListItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = [
            "article_number", "title", "quantity", "price_each", "price_total",
            "image_url", "supplier_name", "shop_url",
        ]
        widgets = {
            "article_number": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "price_each": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "id": "id_price_each"}),
            "price_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "id": "id_price_total"}),
            "image_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://…"}),
            "supplier_name": forms.TextInput(attrs={"class": "form-control"}),
            "shop_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://…"}),
        }
