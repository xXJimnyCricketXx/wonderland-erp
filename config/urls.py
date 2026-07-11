from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from orders.views import ReviewListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("artikel/", include("catalog.urls")),
    path("bestellungen/", include("orders.urls")),
    path("bewertungen/", ReviewListView.as_view(), name="review_list"),
    path("kontakte/", include("contacts.urls")),
    path("termine/", include("appointments.urls")),
    path("einstellungen/", include("settings_hub.urls")),
    path("import/", include("data_import.urls")),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
