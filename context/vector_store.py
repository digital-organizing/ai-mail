from typing import List, cast

from django.db import transaction
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    Hit,
    Hits,
    SearchResult,
    utility,
)

from context.embeddings import EmbeddingModel
from context.models import Realm, Sentence
from context.services import extract_context


def collection_exists(collection_name: str) -> bool:
    """Indicate whether the collection exists or not."""
    value = utility.has_collection(collection_name)
    assert isinstance(value, bool)
    return value


def list_collections() -> List[str]:
    """List name of all existing collections."""
    value = utility.list_collections()
    return cast(list[str], value)


def init_collection(realm_slug):
    """Initialize collection for this realm, skip if it already exists."""
    realm = Realm.objects.get(slug=realm_slug)
    text_id = FieldSchema(name="text_id", dtype=DataType.INT64, is_primary=True)
    text_embedding = FieldSchema(
        name="text_embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=realm.embedding_dimension,
    )
    schema = CollectionSchema(fields=[text_id, text_embedding])
    collection = Collection(name=realm_slug, schema=schema)

    return collection


def store_embeddings(realm_slug, embeddings, ids):
    """Stores the given embeddings in the realm, using the given labels as id."""
    if not utility.has_collection(realm_slug):
        raise ValueError(f"Collection with name {realm_slug} does not exist!")
    collection = Collection(name=realm_slug)
    collection.insert([ids, embeddings])


def index_collection(realm_slug, M=64, ef_construction=128):
    """Recreate the index."""
    collection = Collection(realm_slug)

    collection.flush()
    collection.release()
    collection.drop_index()

    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"efConstruction": 128, "M": 64},
    }

    collection.create_index(field_name="text_embedding", index_params=index_params)


def query_single(realm_slug, embedding, n: int = 5):
    """Search the closes neighbors to the given embedding."""
    return query_multiple(realm_slug, [embedding], n)


def query_multiple(realm_slug, embeddings, n):
    """Search multiple queries at once."""
    collection = Collection(name=realm_slug)

    collection.load()
    search_params = {"metric_type": "COSINE", "params": {"ef": n * 2}}

    results = cast(
        SearchResult,
        collection.search(
            embeddings,
            anns_field="text_embedding",
            param=search_params,
            limit=n,
            output_fields=["text_id"],
        ),
    )

    return cast(Hits, results[0])


def search_context(query: str, realm: Realm, k: int = 5, **settings) -> List[Hit]:
    model = EmbeddingModel(realm.embedding_model, realm.language)
    embedding = model.get_embedding(query)
    return query_single(realm.slug, embedding, n=k)


def get_sentences(results: List[Hit], context_length=120):
    sentences = Sentence.objects.filter(pk__in=[hit.id for hit in results])

    for sentence in sentences:
        yield extract_context(
            sentence.document.content,
            sentence.start_position,
            sentence.length,
            context_length,
        )


@transaction.atomic
def reset_collection(realm_slug):
    """Restes the collection at this name."""
    realm = Realm.objects.get(slug=realm_slug)
    realm.document_set.update(indexed_at=None)

    utility.drop_collection(realm_slug)
