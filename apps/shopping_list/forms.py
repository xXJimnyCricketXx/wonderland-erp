from django import forms
from django.forms import inlineformset_factory

from contacts.models import Supplier

from .models import ShoppingListItem, ShoppingListItemImage


class ShoppingListItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = [
            "article_number", "title", "description", "quantity", "price_each", "price_total",
            "supplier", "shop_url",
        ]
        widgets = {
            "article_number": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "price_each": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "id": "id_price_each"}),
            "price_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "id": "id_price_total"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "shop_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(is_archived=False).order_by("last_name", "first_name")
        self.fields["supplier"].required = False


# Bis zu 5 Bild-Links pro Eintrag, das erste (niedrigste Reihenfolge) ist das
# Vorschaubild in der Tabelle - gleiches dynamisches Add-Muster wie beim
# Inspirationboard (siehe wishlist.forms.WishlistItemImageFormSet), hier
# aber ohne Datei-Upload, nur Link.
ShoppingListItemImageFormSet = inlineformset_factory(
    ShoppingListItem,
    ShoppingListItemImage,
    fields=["image_url", "position"],
    widgets={
        "image_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://…"}),
        "position": forms.NumberInput(attrs={"class": "form-control"}),
    },
    extra=0,
    max_num=5,
    can_delete=True,
)
