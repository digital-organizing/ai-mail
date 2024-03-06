from django.contrib import admin

from classifier.models import Classifier, Sample
from classifier.tasks import train_classifier_task


class SampleInline(admin.TabularInline):
    model = Sample


# Register your models here.
#
@admin.register(Classifier)
class ClassifierAdmin(admin.ModelAdmin):
    inlines = [SampleInline]
    actions = ["train"]

    @admin.action(description="train")
    def train(self, request, queryset):
        for classifier in queryset:
            train_classifier_task(classifier.pk)
