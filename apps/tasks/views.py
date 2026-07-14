from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from core.htmx_utils import htmx_redirect
from core.notifications import color_for_level

from .forms import TaskForm
from .models import STATUS_CHOICES, Task

COLUMN_LEVELS = {"todo": "info", "in_progress": "warning", "done": "success"}


class TaskBoardView(LoginRequiredMixin, View):
    template_name = "tasks/board.html"

    def get(self, request):
        tasks = Task.objects.filter(is_archived=False).select_related(
            "assigned_to", "related_order"
        ).prefetch_related("tags")

        columns = []
        for value, label in STATUS_CHOICES:
            bg, fg = color_for_level(COLUMN_LEVELS.get(value, "info"))
            columns.append({
                "status": value,
                "label": label,
                "tasks": [t for t in tasks if t.status == value],
                "bg_color": bg,
                "fg_color": fg,
            })
        return render(request, self.template_name, {"columns": columns, "today": date.today()})


class TaskModalMixin(LoginRequiredMixin):
    model = Task
    form_class = TaskForm
    template_name = "tasks/_task_modal.html"

    def form_valid(self, form):
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        self.object = form.save()
        return htmx_redirect(self.request, reverse("tasks:board"))


class TaskCreateView(TaskModalMixin, CreateView):
    pass


class TaskUpdateView(TaskModalMixin, UpdateView):
    pass


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/_task_detail_modal.html"


class TaskStatusUpdateView(LoginRequiredMixin, SingleObjectMixin, View):
    """Called from the Kanban board's drag & drop JS (plain fetch, not
    htmx) whenever a card is dropped into a different column."""

    model = Task

    def post(self, request, *args, **kwargs):
        valid_statuses = {value for value, _ in STATUS_CHOICES}
        status = request.POST.get("status")
        if status not in valid_statuses:
            return HttpResponse(status=400)
        task = self.get_object()
        task.status = status
        task.updated_by = request.user
        task.save(update_fields=["status", "updated_by", "updated_at"])
        return HttpResponse(status=204)


class TaskArchiveView(LoginRequiredMixin, SingleObjectMixin, View):
    model = Task

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        task.archive()
        return htmx_redirect(request, reverse("tasks:board"))
