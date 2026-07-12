from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from orders.views import ReviewListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("profil/", include("accounts.urls")),
    path("artikel/", include("catalog.urls")),
    path("bestellungen/", include("orders.urls")),
    path("bewertungen/", ReviewListView.as_view(), name="review_list"),
    path("kontakte/", include("contacts.urls")),
    path("termine/", include("appointments.urls")),
    path("aufgaben/", include("tasks.urls")),
    path("infothek/", include("knowledge.urls")),
    path("infothek/heilsteine/", include("lexikon.urls")),
    path("wunschliste/", include("wishlist.urls")),
    path("dokumente/", include("documents.urls")),
    path("einstellungen/", include("settings_hub.urls")),
    path("import/", include("data_import.urls")),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
