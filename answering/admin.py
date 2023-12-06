from typing import cast

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django_json_widget.widgets import JSONEditorWidget

from answering.models import (
    Inbox,
    InputMessage,
    OutputMessage,
    OutputWebhook,
    SampleTask,
    TaskTemplate,
)


@admin.register(OutputWebhook)
class WebhookAdmin(admin.ModelAdmin):
    pass


class SampleInline(admin.StackedInline):
    model = SampleTask
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {"widget": JSONEditorWidget},
    }


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    inlines = [SampleInline]
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {"widget": JSONEditorWidget},
    }


class TaskInline(admin.StackedInline):
    model = TaskTemplate
    extra = 3
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {"widget": JSONEditorWidget},
    }


@admin.register(Inbox)
class InboxAdmin(admin.ModelAdmin):
    inlines = [TaskInline]
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {"widget": JSONEditorWidget},
    }

    def get_queryset(self, request: HttpRequest) -> QuerySet[Inbox]:
        user: User = cast(User, request.user)
        qs = super().get_queryset(request)

        if user.is_superuser:
            return qs

        return qs.filter(group__in=user.groups.all())


@admin.register(OutputMessage)
class OutputMessageAdmin(admin.ModelAdmin):
    list_filter = ["input__inbox"]
    list_display = ["created", "created", "subject"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[OutputMessage]:
        user = cast(User, request.user)
        qs = super().get_queryset(request)
        if user.is_superuser:
            return qs
        return qs.filter(inbox__group__in=user.groups.all())


@admin.register(InputMessage)
class InputMessageAdmin(admin.ModelAdmin):
    list_filter = ["inbox"]
    list_display = ["created"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[InputMessage]:
        qs = super().get_queryset(request)
        user = cast(User, request.user)
        if user.is_superuser:
            return qs

        return qs.filter(input__inbox__group__in=user.groups.all())
