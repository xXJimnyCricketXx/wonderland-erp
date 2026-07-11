from .notifications import get_all_notifications


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    items = get_all_notifications(request)
    return {
        "notifications": items,
        "notification_count": len(items),
    }
