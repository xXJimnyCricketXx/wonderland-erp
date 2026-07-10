"""Explicit, FK-safe deletion order for the Danger Zone database reset -
children before parents (e.g. Order.customer is on_delete=PROTECT, so
Customer can't be deleted while Orders still reference it).

django.contrib.auth (Users/Groups), sessions, contenttypes, admin log and
BackupSettings are deliberately NOT included - accounts and backup config
survive a reset."""

from catalog.models import Article
from contacts.models import Customer, Supplier, SupplierDiscountTier
from finance.models import AccountMapping, Expense, LedgerEntry, SKR03Account
from knowledge.models import CustomsTariffCode, KnowledgeEntry, PackagingType, ShippingOption
from orders.models import Order, OrderItem, Review
from tasks.models import Task
from wishlist.models import WishlistItem, WishlistItemImage

from core.models import ReferenceOption

from .models import CompanyProfile

RESET_MODEL_ORDER = [
    LedgerEntry,
    Expense,
    AccountMapping,
    SKR03Account,
    Task,
    WishlistItemImage,
    WishlistItem,
    Review,
    OrderItem,
    Order,
    Article,  # variants cascade automatically via parent_article
    SupplierDiscountTier,
    Supplier,
    Customer,
    KnowledgeEntry,
    PackagingType,
    ShippingOption,
    CustomsTariffCode,
    ReferenceOption,
    CompanyProfile,
]
