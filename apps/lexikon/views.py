from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect

from .forms import GemstoneForm
from .models import Gemstone


class GemstoneDetailModalView(LoginRequiredMixin, DetailView):
    model = Gemstone
    template_name = "lexikon/_gemstone_detail_modal.html"
    context_object_name = "gemstone"


class GemstoneModalMixin(LoginRequiredMixin):
    model = Gemstone
    form_class = GemstoneForm
    template_name = "lexikon/_gemstone_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("knowledge:infothek") + "?tab=heilsteine")


class GemstoneCreateView(GemstoneModalMixin, CreateView):
    pass


class GemstoneUpdateView(GemstoneModalMixin, UpdateView):
    pass


class GemstoneDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Gemstone

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, reverse("knowledge:infothek") + "?tab=heilsteine")
