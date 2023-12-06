from django.urls import path

from answering.views import index_view, message_overview, task_template_view

app_name = "answering"

urlpatterns = [
    path("task/<int:pk>/", task_template_view, name="task-view"),
    path("messages/<uuid:pk>/", message_overview, name="messages"),
    path("", index_view, name="index"),
]
