from django.urls import path

from answering.views import index_view, task_template_view

app_name = "answering"

urlpatterns = [
    path("task/<int:pk>/", task_template_view, name="task-view"),
    path("", index_view, name="index"),
]
