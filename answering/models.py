from uuid import uuid4

from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel

from context.models import Realm

# Create your models here.


class Inbox(models.Model):
    uuid = models.UUIDField(default=uuid4, primary_key=True)
    secret = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    group = models.ForeignKey(Group, models.CASCADE)
    tasks: models.QuerySet["TaskTemplate"]

    def __str__(self) -> str:
        return self.name


class OutputWebhook(models.Model):
    class Auth(models.TextChoices):
        DIGEST = "digest", _("Digest")
        BASIC = "basic", _("Basic")
        NONE = "none", _("None")

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=1000)
    headers = models.JSONField(default=dict)

    auth_type = models.CharField(
        max_length=120, choices=Auth.choices, default=Auth.NONE
    )

    auth_user = models.CharField(max_length=120)
    auth_credential = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.name


class TaskTemplate(models.Model):
    inbox = models.ForeignKey(Inbox, models.CASCADE, related_name="tasks")
    webhook = models.ForeignKey(OutputWebhook, models.CASCADE, blank=True, null=True)
    fallback = models.BooleanField()

    name = models.CharField(max_length=300)

    generate_answer = models.BooleanField()

    lepton_url = models.CharField(max_length=1000, blank=True)
    model_config = models.JSONField(default=dict)

    prompt_template = models.TextField(blank=True)

    default_answer = models.TextField(blank=True)

    max_tokens = models.IntegerField(default=720)

    realm = models.ForeignKey(Realm, models.CASCADE, blank=True, null=True)

    samples: models.QuerySet["SampleTask"]

    def __str__(self) -> str:
        return self.name


class SampleTask(models.Model):
    template = models.ForeignKey(TaskTemplate, models.CASCADE, related_name="samples")

    subject = models.CharField(max_length=1024)
    content = models.TextField()

    def __str__(self) -> str:
        return self.subject


class InputMessage(TimeStampedModel):
    inbox = models.ForeignKey(Inbox, models.CASCADE)

    subject = models.CharField(max_length=1024)
    content = models.TextField()

    sender = models.EmailField(blank=True)

    processed_at = models.DateTimeField(null=True, blank=True)

    errors: models.QuerySet["ProcessError"]

    def __str__(self) -> str:
        return self.subject


class MessageClassification(TimeStampedModel):
    message = models.ForeignKey(InputMessage, models.CASCADE)
    task = models.ForeignKey(TaskTemplate, models.SET_NULL, null=True, blank=True)


class ProcessError(TimeStampedModel):
    message = models.ForeignKey(InputMessage, models.CASCADE, related_name="errors")
    timestamp = models.DateTimeField(auto_now_add=True)

    name = models.TextField()
    trace = models.TextField()


class OutputMessage(TimeStampedModel):
    input = models.ForeignKey(InputMessage, models.CASCADE)
    task = models.ForeignKey(TaskTemplate, models.CASCADE)

    subject = models.CharField(max_length=1024)
    content = models.TextField()
