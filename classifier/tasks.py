from celery.app import shared_task

from classifier.classify import train_classifier
from classifier.models import Classifier


@shared_task
def train_classifier_task(pk):
    model = Classifier.objects.filter(pk=pk).get()
    train_classifier(model)
