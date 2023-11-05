from django.contrib.auth.models import Group
from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.


class Realm(TimeStampedModel):
    """Container for context that can be searched by one query"""

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    language = models.CharField(max_length=10)

    is_public = models.BooleanField()

    embedding_model = models.CharField(
        max_length=130,
        choices=(
            (
                "distiluse-base-multilingual-cased-v1",
                "distiluse-base-multilingual-cased-v1",
            ),
            (
                "paraphrase-multilingual-MiniLM-L12-v2",
                "paraphrase-multilingual-MiniLM-L12-v2",
            ),
            (
                "distiluse-base-multilingual-cased-v2",
                "distiluse-base-multilingual-cased-v2",
            ),
            (
                "paraphrase-multilingual-mpnet-base-v2",
                "paraphrase-multilingual-mpnet-base-v2",
            ),
        ),
        default="paraphrase-multilingual-MiniLM-L12-v2",
    )
    embedding_dimension = models.IntegerField(default=384)
    embedding_seq_length = models.IntegerField(default=200)

    group = models.ForeignKey(Group, models.CASCADE)

    document_set: models.QuerySet["Document"]

    def __str__(self):
        return self.name


class Document(TimeStampedModel):
    """Single document that is retrieved through the search."""

    realm = models.ForeignKey(Realm, models.CASCADE)

    content = models.TextField()
    meta = models.JSONField()

    indexed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.content[:100]


class Sentence(TimeStampedModel):
    start_position = models.IntegerField()
    length = models.IntegerField()

    document = models.ForeignKey(Document, models.CASCADE)


class Crawler(TimeStampedModel):
    realm = models.ForeignKey(Realm, models.CASCADE)
    slug = models.CharField(max_length=120)

    start_urls = models.TextField(max_length=500)
    allowed_domains = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.start_urls
