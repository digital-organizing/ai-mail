from typing import Iterable, List

from django.conf import settings

from classifier.client import Client


class EmbeddingModel:
    def __init__(self, language) -> None:
        self.client = Client(settings.API_HOST, settings.API_HOST, settings.API_SECRET)
        self.client.connect()
        self.language = language

    def get_embedding(self, sentence):
        return self.client.get_embedding(sentence)

    def batch_get_embeddings(self, sentences: List[str]):
        return self.client.get_embedding(sentences)

    def get_document_embeddings(self, document: str):
        return self.get_embedding(document)

    def batch_get_document_embeddings(self, documents: Iterable[str]):
        return self.client.get_embedding(documents)
