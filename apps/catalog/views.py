from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

from contacts.models import Supplier
from core.htmx_utils import htmx_redirect
from core.mixins import BackModalMixin
from core.models import ReferenceOption
from core.sorting import resolve_sort

from .forms import ArticleForm
from .models import Article, EtsyListingMapping, next_wd_sku


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "catalog/article_list.html"
    context_object_name = "articles"
    paginate_by = 20

    ALLOWED_SORT_FIELDS = {
        "sku", "title", "category", "price", "stock_quantity",
        "supplier__last_name", "is_active",
    }

    def get_queryset(self):
        # Variants show up on their parent's detail page, not as their own
        # row in the main table. Archived articles are hidden by default -
        # "archive, don't delete" - rather than gone from the list entirely.
        qs = Article.objects.filter(
            parent_article__isnull=True, is_archived=False
        ).select_related("supplier")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(sku__icontains=query))

        is_active = self.request.GET.get("is_active")
        if is_active in ("1", "0"):
            qs = qs.filter(is_active=bool(int(is_active)))

        supplier_id = self.request.GET.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        sort = resolve_sort(self.request, self.ALLOWED_SORT_FIELDS, "title")
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.filter(is_archived=False).order_by("last_name", "first_name")
        context["categories"] = ReferenceOption.objects.filter(
            category="article_category"
        ).order_by("order", "value")
        context["query"] = self.request.GET.get("q", "")
        context["selected_is_active"] = self.request.GET.get("is_active", "")
        context["selected_supplier"] = self.request.GET.get("supplier", "")
        context["selected_supplier_obj"] = (
            Supplier.objects.filter(pk=context["selected_supplier"]).first() if context["selected_supplier"] else None
        )
        context["selected_category"] = self.request.GET.get("category", "")
        context["trash_count"] = Article.objects.filter(
            is_archived=True, parent_article__isnull=True
        ).count()
        return context


class ArticleDetailModalView(BackModalMixin, LoginRequiredMixin, DetailView):
    """Read-only 'product page' shown by the eye icon - a real detail view,
    not the edit form. Its footer links into ArticleUpdateView for editing."""

    model = Article
    template_name = "catalog/_article_detail_modal.html"
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Reviews only attach to Order, not Article, and Etsy gives no way
        # to tell which review-row within a multi-item order belongs to which
        # item - so only single-item orders can be attributed unambiguously.
        from orders.models import Review

        single_item_order_ids = [
            item.order_id
            for item in self.object.order_items.select_related("order").all()
            if item.order.items.count() == 1
        ]
        context["reviews"] = Review.objects.filter(
            order_id__in=single_item_order_ids
        ).order_by("-date_reviewed")
        return context


class ArticleModalMixin(BackModalMixin, LoginRequiredMixin):
    """Shared by create/update: both render into the same modal partial and,
    on success, tell HTMX to do a full-page redirect back to the list rather
    than trying to patch the table in place."""

    model = Article
    form_class = ArticleForm
    template_name = "catalog/_article_modal.html"

    def form_valid(self, form):
        self.object = form.save()
        return htmx_redirect(self.request, reverse("catalog:list"))


class ArticleCreateView(ArticleModalMixin, CreateView):
    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not self.object.sku:
            self.object.sku = next_wd_sku()
        self.object.save()
        return htmx_redirect(self.request, reverse("catalog:list"))


class ArticleUpdateView(ArticleModalMixin, UpdateView):
    pass


class ArticleArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    """Delete action archives instead of removing the row - see Archivable.
    Permanent deletion only happens from the Papierkorb (trash) view."""

    model = Article

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        article.archive()
        return htmx_redirect(request, reverse("catalog:list"))


class EtsyListingMappingListView(LoginRequiredMixin, ListView):
    """One-time "this Etsy listing = this Article" mapping, keyed by Etsy's
    stable Listing ID - see EtsyListingMappingUpdateView for how setting it
    here retroactively fixes every past order for that listing too."""

    model = EtsyListingMapping
    template_name = "catalog/listing_mapping_list.html"
    context_object_name = "mappings"

    def get_queryset(self):
        return EtsyListingMapping.objects.select_related("article").order_by("item_name")

    def get_context_data(self, **kwargs):
        from difflib import SequenceMatcher

        from orders.models import OrderItem

        context = super().get_context_data(**kwargs)
        counts = dict(OrderItem.objects.values_list("listing_id").annotate(n=Count("id")))
        articles = list(Article.objects.filter(is_archived=False, parent_article__isnull=True))

        for mapping in context["mappings"]:
            mapping.order_item_count = counts.get(mapping.listing_id, 0)
            mapping.suggested_article = None
            mapping.suggested_score = 0
            # Gemstone names/"tumbled stone"-type suffixes are close enough
            # between English (Etsy's item name) and German (our Artikel
            # title) that plain string similarity finds a lot of correct
            # matches - still just a one-click suggestion, never auto-saved.
            if not mapping.article and mapping.item_name and articles:
                best = max(
                    articles,
                    key=lambda a: SequenceMatcher(None, mapping.item_name.lower(), a.title.lower()).ratio(),
                )
                score = SequenceMatcher(None, mapping.item_name.lower(), best.title.lower()).ratio()
                if score >= 0.5:
                    mapping.suggested_article = best
                    mapping.suggested_score = round(score * 100)

        # Most-ordered listings first - covers the most orders for the
        # least manual clicks instead of working through them alphabetically.
        context["mappings"] = sorted(context["mappings"], key=lambda m: -m.order_item_count)
        context["articles"] = Article.objects.filter(is_archived=False).order_by("title")

        total_items = sum(m.order_item_count for m in context["mappings"])
        mapped_items = sum(m.order_item_count for m in context["mappings"] if m.article_id)
        context["progress_percent"] = round(mapped_items / total_items * 100) if total_items else 0
        context["mapped_items"] = mapped_items
        context["total_items"] = total_items
        return context


class EtsyListingMappingUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from orders.models import OrderItem

        mapping = get_object_or_404(EtsyListingMapping, pk=pk)
        article_id = request.POST.get("article") or None
        mapping.article_id = article_id
        mapping.save(update_fields=["article"])

        updated = OrderItem.objects.filter(listing_id=mapping.listing_id).update(article=mapping.article)
        messages.success(request, f"„{mapping.item_name}“: {updated} Bestellposition(en) aktualisiert.")
        return redirect(reverse("catalog:listing_mappings"))
