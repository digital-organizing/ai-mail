import itertools
from typing import Iterable, List

from sentence_transformers import SentenceTransformer

from context.services import split_sentences, split_sentences_pos


class EmbeddingModel:
    def __init__(self, model, language) -> None:
        self.model = SentenceTransformer(model)
        self.language = language

    def get_embedding(self, sentence):
        return self.model.encode(sentence)

    def batch_get_embeddings(self, sentences: List[str]):
        return self.model.encode(sentences)

    def get_document_embeddings(self, document: str):
        sentences = split_sentences(document, self.language)
        return self.batch_get_embeddings(sentences)

    def batch_get_document_embeddings(self, documents: Iterable[str]):
        splits = [
            split_sentences_pos(document, self.language) for document in documents
        ]

        flat_embeddings = self.batch_get_embeddings(
            list(itertools.chain(*[split[1] for split in splits]))
        )

        idx = 0
        for split in splits:
            positions, sentences = split
            embeddings = flat_embeddings[idx : idx + len(sentences)]
            yield (positions, sentences, embeddings)
            idx += len(sentences)
