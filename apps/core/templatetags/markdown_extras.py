"""Leichtgewichtige Markdown-Unterstuetzung fuer freie Beschreibungsfelder
(z.B. Einkaufsliste) - gleiches Prinzip wie astro.services.text_render:
markdown macht daraus HTML, bleach saeubert es auf eine feste Tag-Liste,
damit kein beliebiges HTML/Skript ueber ein Textfeld eingeschleust werden
kann."""

import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = ["p", "strong", "em", "h1", "h2", "h3", "ul", "ol", "li", "br", "a"]
ALLOWED_ATTRIBUTES = {"a": ["href"]}


@register.filter(name="markdown_safe")
def markdown_safe(text):
    html = bleach.clean(markdown.markdown(text or ""), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return mark_safe(html)
