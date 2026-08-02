from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect

from .forms import ShoppingListItemForm
from .models import ShoppingListItem


class ShoppingListView(LoginRequiredMixin, ListView):
    model = ShoppingListItem
    template_name = "shopping_list/shopping_list.html"
    context_object_name = "items"
    paginate_by = None

    def get_queryset(self):
        qs = ShoppingListItem.objects.filter(is_archived=False)
        supplier = self.request.GET.get("haendler")
        if supplier:
            qs = qs.filter(supplier_name=supplier)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aus den tatsaechlich vorhandenen Eintraegen abgeleitet, nicht aus
        # Referenzdaten - Haendler wird hier frei eingetippt, nicht aus einer
        # gepflegten Liste gewaehlt (siehe ShoppingListItem.supplier_name).
        context["suppliers"] = (
            ShoppingListItem.objects.filter(is_archived=False)
            .exclude(supplier_name="")
            .order_by("supplier_name")
            .values_list("supplier_name", flat=True)
            .distinct()
        )
        selected_supplier = self.request.GET.get("haendler", "")
        context["selected_supplier"] = selected_supplier
        context["price_total_sum"] = sum(
            (item.price_total for item in context["items"] if item.price_total), 0
        )
        context["trash_count"] = ShoppingListItem.objects.filter(is_archived=True).count()
        return context


class ShoppingListItemModalMixin(LoginRequiredMixin):
    model = ShoppingListItem
    form_class = ShoppingListItemForm
    template_name = "shopping_list/_shopping_list_item_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("shopping_list:list"))


class ShoppingListItemCreateView(ShoppingListItemModalMixin, CreateView):
    pass


class ShoppingListItemUpdateView(ShoppingListItemModalMixin, UpdateView):
    pass


class ShoppingListItemArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = ShoppingListItem

    def post(self, request, *args, **kwargs):
        self.get_object().archive()
        return htmx_redirect(request, reverse("shopping_list:list"))
