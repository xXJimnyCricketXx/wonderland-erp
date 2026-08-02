from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from contacts.models import Supplier
from core.htmx_utils import htmx_redirect
from core.mixins import BackModalMixin

from .forms import ShoppingListItemForm, ShoppingListItemImageFormSet
from .models import ShoppingListItem


class ShoppingListView(LoginRequiredMixin, ListView):
    model = ShoppingListItem
    template_name = "shopping_list/shopping_list.html"
    context_object_name = "items"
    paginate_by = None

    def get_queryset(self):
        qs = ShoppingListItem.objects.filter(is_archived=False).select_related("supplier").prefetch_related("images")
        supplier_id = self.request.GET.get("haendler")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aus den tatsaechlich vorhandenen Eintraegen abgeleitet, nicht alle
        # Lieferanten - sonst waere die Filterliste voller Haendler ohne
        # einen einzigen Eintrag auf der Liste.
        selected_supplier = self.request.GET.get("haendler", "")
        context["suppliers"] = Supplier.objects.filter(
            pk__in=ShoppingListItem.objects.filter(is_archived=False, supplier__isnull=False).values_list("supplier_id", flat=True)
        ).order_by("last_name", "first_name")
        context["selected_supplier"] = selected_supplier
        context["selected_supplier_obj"] = (
            Supplier.objects.filter(pk=selected_supplier).first() if selected_supplier else None
        )
        context["price_total_sum"] = sum(
            (item.price_total for item in context["items"] if item.price_total), 0
        )
        context["trash_count"] = ShoppingListItem.objects.filter(is_archived=True).count()
        return context


class ShoppingListItemDetailModalView(BackModalMixin, LoginRequiredMixin, DetailView):
    """Read-only Ansehen-Ansicht (Bilder + hinterlegte Daten), analog zu
    ArticleDetailModalView - dessen Fusszeile verlinkt in die Bearbeiten-
    Ansicht statt beides zu vermischen."""

    model = ShoppingListItem
    template_name = "shopping_list/_shopping_list_item_detail_modal.html"
    context_object_name = "item"


class ShoppingListItemModalView(LoginRequiredMixin, View):
    """Create/update in one view (nicht zwei generische CBVs), weil das
    Bild-Inline-Formset zusammen mit dem Hauptformular validiert werden muss
    - gleiches Muster wie WishlistItemModalView/OrderModalView."""

    template_name = "shopping_list/_shopping_list_item_modal.html"

    def _get_instance(self, pk):
        return get_object_or_404(ShoppingListItem, pk=pk) if pk else None

    def get(self, request, pk=None):
        item = self._get_instance(pk)
        form = ShoppingListItemForm(instance=item)
        formset = ShoppingListItemImageFormSet(instance=item)
        return self._render(request, form, formset)

    def post(self, request, pk=None):
        item = self._get_instance(pk)
        form = ShoppingListItemForm(request.POST, instance=item)
        formset = ShoppingListItemImageFormSet(request.POST, instance=item or ShoppingListItem())

        if form.is_valid() and formset.is_valid():
            item = form.save()
            formset.instance = item
            formset.save()
            return htmx_redirect(request, reverse("shopping_list:list"))

        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(
            request,
            self.template_name,
            {"form": form, "formset": formset, "object": form.instance if form.instance.pk else None},
        )


class ShoppingListItemArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = ShoppingListItem

    def post(self, request, *args, **kwargs):
        self.get_object().archive()
        return htmx_redirect(request, reverse("shopping_list:list"))
