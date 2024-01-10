from django.conf import settings

from answering.models import Inbox
from classifier.client import connect


def train_inbox_classifier(inbox: Inbox):
    # TODO:
    tasks = inbox.tasks.all()

    labels = []

    samples = []

    for task in tasks:
        label = task.pk

        for sample in task.samples.all():
            samples.append(f"{sample.subject}:\n\n{sample.content}")
            labels.append(label)

    with connect(settings.API_HOST, settings.API_PORT, settings.API_SECRET) as client:
        client.train_classifier(inbox.uuid.hex, samples, labels)


def predict_inbox_task(inbox, subject, message):
    # TODO:
    with connect(settings.API_HOST, settings.API_PORT, settings.API_SECRET) as client:
        client.predict_class(inbox.uuid.hex, f"{subject}:\n\n{{messag}}")
