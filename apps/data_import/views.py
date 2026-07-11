from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ImportView(LoginRequiredMixin, TemplateView):
    template_name = "data_import/import.html"
