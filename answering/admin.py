from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from answering.models import Inbox, OutputWebhook, SampleTask, TaskTemplate


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
