import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from orders.views import ReviewListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("profil/", include("accounts.urls")),
    path("artikel/", include("catalog.urls")),
    path("bestellungen/", include("orders.urls")),
    path("bewertungen/", ReviewListView.as_view(), name="review_list"),
    path("kontakte/", include("contacts.urls")),
    path("finanzen/", include("finance.urls")),
    path("berichte/", include("reports.urls")),
    path("nachrichten/", include("messaging.urls")),
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

# Kein separater Webserver/Reverse-Proxy vor der App (Single-Container-
# Deployment, siehe Dockerfile) - Medien-Dateien muessen daher auch mit
# DEBUG=False (Produktion) ueber Django selbst ausgeliefert werden. Bewusst
# nicht ueber django.conf.urls.static.static(), die trotz Aufruf ohne
# DEBUG=True stets eine leere Liste liefert - hier direkt die Serve-View
# registriert, die dieser Helper intern auch nur weiterreicht.
urlpatterns += [
    re_path(r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")), serve, {"document_root": settings.MEDIA_ROOT}),
]
