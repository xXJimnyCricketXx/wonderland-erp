from django import forms

from .models import CompanyProfile


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
