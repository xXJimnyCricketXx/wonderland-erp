from django import forms

from contacts.models import Customer, Supplier
from core.models import ReferenceOption

from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "title", "start_date", "end_date", "is_all_day", "start_time", "end_time",
            "event_type", "customers", "supplier", "location", "description",
            "has_reminder", "reminder_lead_minutes",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "is_all_day": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}, format="%H:%M"),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "has_reminder": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_has_reminder"}),
            "reminder_lead_minutes": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [("", "---")] + [
            (opt.value, opt.value)
            for opt in ReferenceOption.objects.filter(category="appointment_type").order_by("order", "value")
        ]
        self.fields["event_type"] = forms.ChoiceField(
            choices=choices, required=False, label="Termin-Typ",
            widget=forms.Select(attrs={"class": "form-select"}),
        )

        self.fields["customers"].queryset = Customer.objects.filter(is_archived=False).order_by("last_name", "first_name")
        self.fields["customers"].widget.attrs.update({"class": "form-select", "size": "6"})
        self.fields["supplier"].queryset = Supplier.objects.filter(is_archived=False).order_by("last_name", "first_name")
        self.fields["supplier"].widget.attrs.update({"class": "form-select"})
