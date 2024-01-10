from django.contrib import admin

from classifier.models import Classifier, Sample


class SampleInline(admin.TabularInline):
    model = Sample


# Register your models here.
#
@admin.register(Classifier)
class ClassifierAdmin(admin.ModelAdmin):
    inlines = [SampleInline]
