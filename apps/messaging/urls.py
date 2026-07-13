from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.MessagesView.as_view(), name="index"),
    path("kontakte/", views.ContactListView.as_view(), name="contact_list"),
    path("badge/", views.UnreadBadgeView.as_view(), name="badge"),
    path("<int:user_id>/", views.MessagesView.as_view(), name="conversation"),
    path("<int:user_id>/nachrichten/", views.MessageListView.as_view(), name="message_list"),
    path("<int:user_id>/senden/", views.MessageSendView.as_view(), name="send"),
]
