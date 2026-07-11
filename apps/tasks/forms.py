from django import forms
from django.contrib.auth import get_user_model

from core.models import ReferenceOption
from orders.models import Order

from .models import Task

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title", "description", "due_date", "status",
            "tags", "assigned_to", "related_order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "status": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select", "size": "4"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "related_order": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tags"].queryset = ReferenceOption.objects.filter(category="task_tag").order_by("order", "value")
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["assigned_to"].required = False
        self.fields["related_order"].queryset = Order.objects.filter(is_archived=False).order_by("-sale_date")
        self.fields["related_order"].required = False
