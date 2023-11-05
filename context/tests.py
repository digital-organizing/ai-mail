from django.contrib.auth.models import Group
from django.test import TestCase
from scrapy.crawler import CrawlerProcess

from context.crawler import ParagraphsSpider
from context.embeddings import EmbeddingModel
from context.models import Document, Realm, Sentence
from context.services import extract_context
from context.tasks import import_embeddings, import_jsonl
from context.vector_store import (
    collection_exists,
    get_sentences,
    init_collection,
    reset_collection,
    search_context,
)

# Create your tests here.


class TestVectorStore(TestCase):
    def test_open_connection(self):
        assert not collection_exists("test")

    def test_create_embeddings(self):
        model = EmbeddingModel("paraphrase-multilingual-MiniLM-L12-v2", "german")
        model.batch_get_document_embeddings(
            [
                "This is my first test",
                "This is the second test, and so on. But this has two sentences.",
            ]
        )

    def test_simple_site(self):
        process = CrawlerProcess(
            settings={"FEEDS": {"test.jsonl": {"format": "jsonlines"}}}
        )
        process.crawl(
            ParagraphsSpider,
            name="test-crawler",
            allowed_domains=["sacovo.ch"],
            start_urls=["https://sacovo.ch"],
        )

        process.start()
        realm = Realm.objects.create(
            name="Test",
            slug="test",
            language="german",
            is_public=True,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            embedding_dimension=384,
            embedding_seq_length=200,
            group=Group.objects.create(name="Test"),
        )

        import_jsonl("test.jsonl", realm)

    def test_import_documents(self):
        realm = Realm.objects.create(
            name="Test Import",
            slug="test_import",
            language="german",
            is_public=True,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            embedding_dimension=384,
            embedding_seq_length=200,
            group=Group.objects.create(name="Test"),
        )

        content = "Until recently, the prevailing view assumed lorem ipsum was born as a nonsense text. “It's not Latin, though it looks like it, and it actually says nothing,” Before & After magazine answered a curious reader, “Its ‘words’ loosely approximate the frequency with which letters occur in English, which is why at a glance it looks pretty real.”"

        doc = Document.objects.create(
            realm=realm,
            content=content,
            meta={},
        )

        init_collection(realm.slug)
        import_embeddings(realm.slug)
        result = search_context("Lorem ipsum is nonsense.", realm, k=1)
        assert len(result) == 1

        s = Sentence.objects.get(document=doc, start_position=0)

        assert result[0].id == s.pk

        for sentence in get_sentences(result, 120):
            self.assertEqual(sentence, content[:120])

        reset_collection(realm.slug)

    def test_extract_sentence(self):
        sentence = "Until recently, the prevailing view assumed lorem ipsum was born as a nonsense text."

        self.assertEqual(
            sentence, extract_context(sentence, 0, len(sentence), len(sentence))
        )
        self.assertEqual(sentence[:20], extract_context(sentence, 0, len(sentence), 20))
