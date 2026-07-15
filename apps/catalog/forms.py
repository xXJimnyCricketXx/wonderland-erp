from django import forms
from django.forms import inlineformset_factory

from contacts.models import Supplier
from core.models import ReferenceOption

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title", "sku", "category", "supplier", "is_active", "is_sold_out",
            "price", "currency_code", "stock_quantity", "minimum_stock_quantity",
            "description", "thumbnail_url", "shop_url",
            "purchase_price_per_unit", "purchase_price_unit_label", "purchase_price_per_piece",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_sold_out": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "currency_code": forms.TextInput(attrs={"class": "form-control"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "minimum_stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "thumbnail_url": forms.URLInput(attrs={"class": "form-control"}),
            "shop_url": forms.URLInput(attrs={"class": "form-control"}),
            "purchase_price_per_unit": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "purchase_price_unit_label": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_price_per_piece": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Category options come from the Referenzdaten table, not a hardcoded
        # enum, so they're loaded fresh on every form render.
        category_choices = [("", "---")] + [
            (opt.value, opt.value)
            for opt in ReferenceOption.objects.filter(category="article_category").order_by("order", "value")
        ]
        self.fields["category"] = forms.ChoiceField(
            choices=category_choices,
            required=False,
            label="Kategorie",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        self.fields["supplier"].queryset = Supplier.objects.filter(is_archived=False).order_by("last_name", "first_name")
        self.fields["supplier"].widget.attrs.update({"class": "form-select"})


# Varianten sind selbst ganz normale Article-Zeilen (self-FK parent_article),
# hier aber als Etsy-artige Tabelle im "Variationen"-Pill des Hauptartikels
# editierbar statt einzeln ueber die Artikel-Liste (die zeigt nur Hauptartikel).
ArticleVariantFormSet = inlineformset_factory(
    Article,
    Article,
    fk_name="parent_article",
    fields=["variant_label", "sku", "price", "stock_quantity", "thumbnail_url", "is_active", "is_sold_out"],
    widgets={
        "variant_label": forms.TextInput(attrs={"class": "form-control", "placeholder": "z.B. Sorte: Amethyst"}),
        "sku": forms.TextInput(attrs={"class": "form-control"}),
        "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
        "thumbnail_url": forms.URLInput(attrs={"class": "form-control"}),
        "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        "is_sold_out": forms.CheckboxInput(attrs={"class": "form-check-input"}),
    },
    extra=0,
    can_delete=True,
)
