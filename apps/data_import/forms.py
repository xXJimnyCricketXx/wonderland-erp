from django import forms

from knowledge.models import PackagingLicenseDataReport


class ArticleImportForm(forms.Form):
    file = forms.FileField(
        label="Etsy-Listing-CSV",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )


class OrderImportForm(forms.Form):
    file = forms.FileField(
        label="Etsy-Sold-Orders-CSV",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )


class OrderItemImportForm(forms.Form):
    file = forms.FileField(
        label="Etsy-Sold-Order-Items-CSV",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )


class ReviewImportForm(forms.Form):
    file = forms.FileField(
        label="reviews.json",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".json"}),
    )


class PackagingLicenseXmlImportForm(forms.Form):
    recipient = forms.ChoiceField(
        label="Empfänger", choices=PackagingLicenseDataReport.RECIPIENT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    file = forms.FileField(
        label="Datenmeldung-XML",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".xml"}),
    )
