from uuid import uuid4

from django.db import models

# Create your models here.


class Classifier(models.Model):
    name = models.CharField(max_length=120)
    uuid = models.UUIDField(default=uuid4)

    model = models.FileField(upload_to="models/", blank=True)

    language = models.CharField(max_length=20)

    min_threshold = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class Sample(models.Model):
    content = models.TextField()
    label = models.CharField(max_length=500)
    classifier = models.ForeignKey(Classifier, models.CASCADE)

    def __str__(self):
        return self.label
