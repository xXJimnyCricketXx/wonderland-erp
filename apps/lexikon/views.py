from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
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
        self.object = form.save(commit=False)
        image = form.cleaned_data.get("image")
        if image:
            self.object.image_data = image.read()
            self.object.image_content_type = image.content_type
            self.object.image_filename = image.name
        elif form.cleaned_data.get("remove_image"):
            self.object.image_data = None
            self.object.image_content_type = ""
            self.object.image_filename = ""
        self.object.save()
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


class GemstoneImageView(LoginRequiredMixin, View):
    """Liefert das Bild direkt aus der Lexikon-DB (Blob) statt aus MEDIA_ROOT
    - siehe Gemstone.image_data."""

    def get(self, request, pk):
        gemstone = get_object_or_404(Gemstone, pk=pk)
        if not gemstone.image_data:
            raise Http404
        return HttpResponse(bytes(gemstone.image_data), content_type=gemstone.image_content_type or "application/octet-stream")
