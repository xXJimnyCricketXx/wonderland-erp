from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, View
from django.views.generic.detail import DetailView, SingleObjectMixin

from core.htmx_utils import htmx_redirect
from core.mixins import BackModalMixin
from core.models import ReferenceOption
from core.sorting import resolve_sort

from .forms import CustomerForm, SupplierDiscountTierFormSet, SupplierForm
from .models import Customer, Supplier

CUSTOMER_SORT_FIELDS = {"last_name", "first_name", "email", "status", "is_returning_customer"}
SUPPLIER_SORT_FIELDS = {"last_name", "first_name", "company_name", "platform__last_name", "status"}


class ContactListView(LoginRequiredMixin, View):
    """One page, two tabs (Kunden/Lieferanten) - the pills are plain links
    (full navigation via ?tab=), not client-side JS toggles, since each tab
    needs its own independent search/sort/pagination and sharing GET params
    for both tables on one page load would collide."""

    template_name = "contacts/kontakte.html"

    def get(self, request):
        tab = "lieferanten" if request.GET.get("tab") == "lieferanten" else "kunden"
        context = self._supplier_context(request) if tab == "lieferanten" else self._customer_context(request)
        context["active_tab"] = tab
        return render(request, self.template_name, context)

    def _paginate(self, request, qs):
        paginator = Paginator(qs, 20)
        return paginator.get_page(request.GET.get("page"))

    def _customer_context(self, request):
        qs = Customer.objects.filter(is_archived=False)

        query = request.GET.get("q", "")
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
                | Q(email__icontains=query) | Q(company_name__icontains=query)
            )

        status = request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)

        returning = request.GET.get("is_returning_customer", "")
        if returning in ("1", "0"):
            qs = qs.filter(is_returning_customer=bool(int(returning)))

        sort = resolve_sort(request, CUSTOMER_SORT_FIELDS, "last_name")
        page_obj = self._paginate(request, qs.order_by(sort))

        return {
            "customers": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "paginator": page_obj.paginator,
            "statuses": ReferenceOption.objects.filter(category="contact_status").order_by("order", "value"),
            "query": query,
            "selected_status": status,
            "selected_returning": returning,
            "trash_count": Customer.objects.filter(is_archived=True).count(),
        }

    def _supplier_context(self, request):
        qs = Supplier.objects.filter(is_archived=False).select_related("platform")

        query = request.GET.get("q", "")
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
                | Q(company_name__icontains=query) | Q(account_number__icontains=query)
            )

        status = request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)

        sort = resolve_sort(request, SUPPLIER_SORT_FIELDS, "last_name")
        page_obj = self._paginate(request, qs.order_by(sort))

        return {
            "suppliers": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "paginator": page_obj.paginator,
            "statuses": ReferenceOption.objects.filter(category="contact_status").order_by("order", "value"),
            "query": query,
            "selected_status": status,
            "trash_count": Supplier.objects.filter(is_archived=True).count(),
        }


class CustomerDetailModalView(BackModalMixin, LoginRequiredMixin, DetailView):
    model = Customer
    template_name = "contacts/_customer_detail_modal.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = self.object.orders.order_by("-sale_date")
        return context


class CustomerModalMixin(LoginRequiredMixin):
    model = Customer
    form_class = CustomerForm
    template_name = "contacts/_customer_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("contacts:list") + "?tab=kunden")


class CustomerCreateView(CustomerModalMixin, CreateView):
    pass


class CustomerUpdateView(CustomerModalMixin, UpdateView):
    pass


class CustomerArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Customer

    def post(self, request, *args, **kwargs):
        customer = self.get_object()
        customer.archive()
        return htmx_redirect(request, reverse("contacts:list") + "?tab=kunden")


class SupplierDetailModalView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = "contacts/_supplier_detail_modal.html"
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["articles"] = self.object.articles.filter(
            parent_article__isnull=True, is_archived=False
        )
        context["discount_tiers"] = self.object.discount_tiers.all()
        return context


class SupplierModalView(LoginRequiredMixin, View):
    """Create/update in one view (not two CBVs) because the discount-tier
    inline formset needs to be validated together with the main form before
    either is saved - Django's generic CreateView/UpdateView don't support
    a second bound formset out of the box."""

    template_name = "contacts/_supplier_modal.html"

    def _get_instance(self, pk):
        return get_object_or_404(Supplier, pk=pk) if pk else None

    def get(self, request, pk=None):
        supplier = self._get_instance(pk)
        form = SupplierForm(instance=supplier)
        formset = SupplierDiscountTierFormSet(instance=supplier)
        return self._render(request, form, formset)

    def post(self, request, pk=None):
        supplier = self._get_instance(pk)
        form = SupplierForm(request.POST, instance=supplier)
        formset = SupplierDiscountTierFormSet(request.POST, instance=supplier or Supplier())

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                supplier = form.save()
                formset.instance = supplier
                formset.save()
            return htmx_redirect(request, reverse("contacts:list") + "?tab=lieferanten")

        return self._render(request, form, formset)

    def _render(self, request, form, formset):
        return render(
            request,
            self.template_name,
            {"form": form, "formset": formset, "object": form.instance if form.instance.pk else None},
        )


class SupplierArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Supplier

    def post(self, request, *args, **kwargs):
        supplier = self.get_object()
        supplier.archive()
        return htmx_redirect(request, reverse("contacts:list") + "?tab=lieferanten")
