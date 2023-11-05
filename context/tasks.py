import json
import os

import tika
from celery.app import shared_task
from django.conf import settings
from django.utils import timezone
from model_utils.models import transaction
from scrapy.crawler import CrawlerProcess

from context.crawler import ParagraphsSpider
from context.embeddings import EmbeddingModel
from context.models import Crawler, Document, Realm, Sentence
from context.vector_store import index_collection, store_embeddings


@shared_task
def run_crawler(crawler_pk):
    tika.initVM()
    crawler = Crawler.objects.get(pk=crawler_pk)
    path = f"{os.path.join(settings.CRAWL_DIR, crawler.slug)}.jsonl"

    process = CrawlerProcess(settings={"FEEDS": {path: {"format": "jsonlines"}}})

    process.crawl(
        ParagraphsSpider,
        name=crawler.slug,
        allowed_domains=crawler.allowed_domains.split("\n"),
        start_urls=crawler.start_urls.split("\n"),
    )

    process.start()
    import_jsonl(path, crawler.realm)


def import_jsonl(path, realm):
    with open(path) as fp:
        for line in fp:
            data = json.loads(line)
            text = data["text"]

            del data["text"]

            Document.objects.create(realm=realm, content=text, meta=data)


@shared_task
@transaction.atomic
def import_embeddings(realm_slug):
    realm = Realm.objects.get(slug=realm_slug)
    documents = realm.document_set.filter(indexed_at__isnull=True)

    document_texts = documents.values_list("content", flat=True)
    document_ids = documents.values_list("id", flat=True)

    model = EmbeddingModel(realm.embedding_model, realm.language)

    for document_id, (positions, sentences, embeddings) in zip(
        document_ids, model.batch_get_document_embeddings(document_texts)
    ):
        objs = []
        used_embeddings = []
        for sentence, position, embedding in zip(sentences, positions, embeddings):
            if len(sentence) < 10:
                continue
            objs.append(
                Sentence(
                    start_position=position,
                    length=len(sentence),
                    document_id=document_id,
                )
            )
            used_embeddings.append(embedding)

        objs = Sentence.objects.bulk_create(objs)
        ids = [obj.pk for obj in objs]
        store_embeddings(realm.slug, used_embeddings, ids)

    index_collection(realm.slug)
    documents.update(indexed_at=timezone.now())
