from django import forms

from .models import Gemstone


class GemstoneForm(forms.ModelForm):
    class Meta:
        model = Gemstone
        fields = [
            "name", "image",
            "description", "alternative_names", "origin", "confusable_with", "counterfeits",
            "mineral_class", "chemical_composition", "formation", "crystal_system",
            "mohs_hardness", "density", "cleavage", "fracture",
            "transparency", "color", "luster", "streak",
            "organ_effect", "physical_effect", "emotional_effect", "application",
            "bach_flower", "astrological_sign", "chakra", "feng_shui", "care_instructions", "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "alternative_names": forms.TextInput(attrs={"class": "form-control"}),
            "origin": forms.TextInput(attrs={"class": "form-control"}),
            "confusable_with": forms.TextInput(attrs={"class": "form-control"}),
            "counterfeits": forms.TextInput(attrs={"class": "form-control"}),
            "mineral_class": forms.TextInput(attrs={"class": "form-control"}),
            "chemical_composition": forms.TextInput(attrs={"class": "form-control"}),
            "formation": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "crystal_system": forms.TextInput(attrs={"class": "form-control"}),
            "mohs_hardness": forms.TextInput(attrs={"class": "form-control", "placeholder": "z.B. 6-7"}),
            "density": forms.TextInput(attrs={"class": "form-control"}),
            "cleavage": forms.TextInput(attrs={"class": "form-control"}),
            "fracture": forms.TextInput(attrs={"class": "form-control"}),
            "transparency": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "luster": forms.TextInput(attrs={"class": "form-control"}),
            "streak": forms.TextInput(attrs={"class": "form-control"}),
            "organ_effect": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "physical_effect": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "emotional_effect": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "application": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "bach_flower": forms.TextInput(attrs={"class": "form-control"}),
            "astrological_sign": forms.TextInput(attrs={"class": "form-control"}),
            "chakra": forms.TextInput(attrs={"class": "form-control"}),
            "feng_shui": forms.TextInput(attrs={"class": "form-control"}),
            "care_instructions": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
