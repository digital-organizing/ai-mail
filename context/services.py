from typing import List, cast

from nltk.data import load
from nltk.tokenize.punkt import PunktSentenceTokenizer


def extract_context(
    text: str, start_position: int, sentence_length: int, context_length: int
) -> str:
    if sentence_length > context_length:
        return text[start_position : start_position + sentence_length][:context_length]

    center = start_position + sentence_length // 2

    start = max(center - context_length // 2, 0)
    end = start + context_length
    return text[start:end]


def split_sentences(content: str, language: str):
    tokenizer: PunktSentenceTokenizer = cast(
        PunktSentenceTokenizer, load(f"tokenizers/punkt/{language}.pickle")
    )

    return tokenizer.tokenize(content)


def split_sentences_pos(content: str, language: str):
    tokenizer: PunktSentenceTokenizer = cast(
        PunktSentenceTokenizer, load(f"tokenizers/punkt/{language}.pickle")
    )

    starts: List[int] = []
    sentences: List[str] = []
    for start, end in tokenizer.span_tokenize(content):
        starts.append(start)
        sentences.append(content[start:end])
    return starts, sentences
