from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from context.models import Crawler, Document, Realm, Sentence
from context.tasks import import_embeddings, run_crawler
from context.vector_store import init_collection


# Register your models here.
@admin.register(Realm)
class RealmAdmin(admin.ModelAdmin):
    actions = ["index_realm", "init_realm"]

    def init_realm(self, request, queryset):
        for realm in queryset:
            init_collection(realm.slug)

    def index_realm(self, request, queryset):
        for realm in queryset:
            import_embeddings.delay(realm.slug)


@admin.register(Crawler)
class CralwerAdmin(admin.ModelAdmin):
    actions = ["start_crawler"]

    def start_crawler(self, request, queryset):
        for crawler in queryset:
            run_crawler.delay(crawler.pk)


class SentenceInline(admin.TabularInline):
    model = Sentence


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {"widget": JSONEditorWidget},
    }
