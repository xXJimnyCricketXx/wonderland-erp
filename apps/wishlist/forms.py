from django import forms
from django.forms import inlineformset_factory

from core.models import ReferenceOption

from .models import WishlistItem, WishlistItemImage


def _build_reference_choicefield(category, label, required=False):
    choices = [("", "---")] + [
        (opt.value, opt.value)
        for opt in ReferenceOption.objects.filter(category=category).order_by("order", "value")
    ]
    return forms.ChoiceField(
        choices=choices, required=required, label=label,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class WishlistItemForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ["title", "notes", "source_url", "estimated_price", "status", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "source_url": forms.URLInput(attrs={"class": "form-control"}),
            "estimated_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select", "size": "4"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"] = _build_reference_choicefield("wishlist_status", "Status", required=True)
        self.fields["tags"].queryset = ReferenceOption.objects.filter(
            category="wishlist_tag"
        ).order_by("order", "value")


WishlistItemImageFormSet = inlineformset_factory(
    WishlistItem,
    WishlistItemImage,
    fields=["image", "image_url", "position"],
    widgets={
        "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        "image_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "...oder Bild-Link"}),
        "position": forms.NumberInput(attrs={"class": "form-control"}),
    },
    extra=0,
    max_num=5,
    can_delete=True,
)
