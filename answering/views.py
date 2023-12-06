import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.shortcuts import render

from answering.forms import InputForm
from answering.models import Inbox, InputMessage, OutputMessage, TaskTemplate
from answering.process import write_answer
from context.models import Sentence
from context.services import extract_context


def incoming_message(request: HttpRequest, uuid):
    inbox = Inbox.objects.get(uuid=uuid)

    if request.headers.get("secret") != inbox.secret:
        raise PermissionDenied()

    data = json.loads(request.body)

    message = InputMessage.objects.create(
        inbox=inbox,
        subject=data.get("subject"),
        content=data.get("content"),
        sender=data.get("sender"),
    )

    return JsonResponse({"id": message.pk})


@login_required
def task_template_view(request, pk: int):
    task_template = TaskTemplate.objects.get(pk=pk)
    inbox = task_template.inbox
    group = task_template.inbox.group

    if not request.user.groups.filter(pk=group.pk).exists():
        raise PermissionDenied("You don't have access to this task")

    form = InputForm()

    if request.method == "POST":
        form = InputForm(request.POST)
        if form.is_valid():
            input = InputMessage.objects.create(
                inbox=task_template.inbox,
                subject=form.cleaned_data["subject"],
                content=form.cleaned_data["content"],
            )
            subject, message, hits = write_answer(
                task_template,
                input.subject,
                input.content,
            )

            results = []
            for result in hits:
                sentence = Sentence.objects.get(pk=result.id)
                results.append(
                    {
                        "distance": result.distance,
                        "sentence": extract_context(
                            sentence.document.content,
                            sentence.start_position,
                            sentence.length,
                            500,
                        ),
                        "id": sentence.pk,
                        "meta": sentence.document.meta,
                    }
                )
            OutputMessage.objects.create(
                input=input,
                task=task_template,
                subject=subject,
                content=message,
            )
            return JsonResponse(
                {"subject": subject, "message": message, "results": results}
            )

    return render(
        request,
        "answering/task_form.html",
        {"form": form, "task": task_template, "inbox": inbox},
    )


def index_view(request):
    return render(request, "index.html", {})


def message_overview(request, pk):
    inbox = Inbox.objects.get(pk=pk)
    group = inbox.group

    if not request.user.groups.filter(pk=group.pk).exists():
        raise PermissionDenied("You don't have access to this task")
    messages = InputMessage.objects.filter(inbox=inbox)

    page_number = request.GET.get("page", 1)
    p = Paginator(messages, 20)

    return render(
        request,
        "answering/messages.html",
        {
            "page": p.get_page(page_number),
            "inbox": inbox,
        },
    )
