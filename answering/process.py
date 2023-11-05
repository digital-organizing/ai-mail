import traceback
from typing import List, Tuple

import requests
from django.conf import settings
from django.template import Context, Template
from django.utils import timezone
from leptonai.client import Client
from pymilvus import Hit

from answering.auth import get_auth
from answering.models import (
    Inbox,
    InputMessage,
    MessageClassification,
    OutputMessage,
    ProcessError,
    TaskTemplate,
)
from classifier.client import connect
from context.vector_store import get_sentences, search_context


def handle_message(input: InputMessage):
    try:
        task = classify_message(input)
        MessageClassification.objects.create(message=input, task=task)
        output = create_output(input, task)
    except Exception as ex:
        trace = traceback.format_exc()
        exception = str(ex)

        ProcessError.objects.create(
            message=input,
            trace=trace,
            exception=exception,
        )
        return

    webhook = output.task.webhook

    output.save()

    if webhook is None:
        return

    requests.post(
        webhook.url,
        json={
            "inbox": output.input.inbox.uuid,
            "subject": output.subject,
            "message": output.content,
            "pk": output.pk,
        },
        headers=webhook.headers,
        auth=get_auth(webhook),
    )

    input.processed_at = timezone.now()
    input.save()


def create_output(input: InputMessage, task: TaskTemplate) -> OutputMessage:
    output = OutputMessage(
        input=input, subject=input.subject, content=input.content, task=task
    )

    if task.generate_answer:
        subject, message, _ = write_answer(task, input.subject, input.content)
        output.subject = subject
        output.content = message

    elif task.default_answer:
        output.content = task.default_answer

    return output


def classify_message(input: InputMessage) -> TaskTemplate:
    inbox = input.inbox

    with connect(
        settings.CLASSIFIER_HOST,
        settings.CALSSIFIER_PORT,
        settings.CLASSIFIER_SECRET,
    ) as client:
        id = client.predict_class(inbox.name, [input.content])
    return inbox.tasks.get(pk=id)


def write_answer(
    node: TaskTemplate, subject: str, content: str
) -> Tuple[str, str, List[Hit]]:
    client = Client(node.lepton_url)

    results = []

    if node.realm:
        results = search_context(content, node.realm, k=3)

        context = "\n".join(get_sentences(results, 500))
    else:
        context = ""

    prompt = Template(node.prompt_template).render(
        context=Context(
            {
                "message": content,
                "subject": subject,
                "context": context,
            }
        )
    )
    message = client.run(inputs=prompt, return_full_text=False, **node.model_config)

    return subject, message.strip(), results


def train_classifier(inbox: Inbox):
    classes = inbox.tasks.all()

    samples, labels = [], []

    for class_ in classes:
        for sample in class_.samples.all():
            samples.append(sample.content)
            labels.append(class_.pk)

    with connect(
        settings.CLASSIFIER_HOST,
        settings.CALSSIFIER_PORT,
        settings.CLASSIFIER_SECRET,
    ) as client:
        client.train_classifier(inbox.name, samples, labels, settings.CLASSIFIER_CONFIG)
