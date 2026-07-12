from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect
from core.models import ReferenceOption

from .forms import WishlistItemForm, WishlistItemImageFormSet
from .models import WishlistItem


class WishlistBoardView(LoginRequiredMixin, View):
    template_name = "wishlist/board.html"

    def get(self, request):
        status = request.GET.get("status", "")
        query = request.GET.get("q", "")

        qs = WishlistItem.objects.all().prefetch_related("images", "tags")
        if status:
            qs = qs.filter(status=status)
        if query:
            qs = qs.filter(title__icontains=query)

        return render(request, self.template_name, {
            "items": qs,
            "statuses": ReferenceOption.objects.filter(category="wishlist_status").order_by("order", "value"),
            "active_status": status,
            "query": query,
        })


class WishlistItemDetailModalView(LoginRequiredMixin, DetailView):
    model = WishlistItem
    template_name = "wishlist/_wishlist_item_detail_modal.html"
    context_object_name = "item"


class WishlistItemModalView(LoginRequiredMixin, View):
    """Create/update in one view (not two CBVs) because the image inline
    formset needs to be validated together with the main form before either
    is saved - Django's generic CreateView/UpdateView don't support a second
    bound formset out of the box."""

    template_name = "wishlist/_wishlist_item_modal.html"

    def _get_instance(self, pk):
        return get_object_or_404(WishlistItem, pk=pk) if pk else None

    def get(self, request, pk=None):
        item = self._get_instance(pk)
        form = WishlistItemForm(instance=item)
        formset = WishlistItemImageFormSet(instance=item)
        return self._render(request, form, formset)

    def post(self, request, pk=None):
        item = self._get_instance(pk)
        form = WishlistItemForm(request.POST, instance=item)
        formset = WishlistItemImageFormSet(request.POST, request.FILES, instance=item or WishlistItem())

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                item = form.save()
                formset.instance = item
                formset.save()
            return htmx_redirect(request, reverse("wishlist:board"))

        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(
            request,
            self.template_name,
            {"form": form, "formset": formset, "object": form.instance if form.instance.pk else None},
        )


class WishlistItemDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    model = WishlistItem

    def post(self, request, *args, **kwargs):
        self.get_object().delete()
        return htmx_redirect(request, reverse("wishlist:board"))
