import hashlib
from typing import Any, Optional

import scrapy
from bs4 import BeautifulSoup
from numba import jit
from scrapy.http import Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from tika import parser

MIN_CONTENT_LENGTH = 120


@jit(nopython=True)
def mean_ord(text: str) -> float:
    total = 0
    count = 0
    for char in text:
        total += ord(char)
        count += 1
    return total / count


class ParagraphsSpider(scrapy.Spider):
    seen_hashes = set()
    link_extractor = LinkExtractor()

    def __init__(self, name: Optional[str] = None, **kwargs: Any):
        self.allowed_domains = kwargs.pop("allowed_domains")
        self.start_urls = kwargs.pop("start_urls")
        super().__init__(name, **kwargs)

    def add_hash(self, text):
        hash = hashlib.md5(text.encode()).hexdigest
        if hash in self.seen_hashes:
            return False
        self.seen_hashes.add(hash)
        return True

    def parse_text(self, response: TextResponse):
        texts = response.xpath(
            "/html/body//*[ self::p | self::strong | self::h1 | self::span]/node()"
        ).getall()

        texts = (BeautifulSoup(text, "lxml").text for text in texts)

        for page, text in enumerate(
            filter(lambda text: len(text) > MIN_CONTENT_LENGTH, texts)
        ):
            if self.add_hash(text):
                yield {"text": text, "page": page + 1, "url": response.url}

        for link in self.link_extractor.extract_links(response):
            url = link.url
            if url.startswith("tel:"):
                continue
            if url.startswith("mailto:"):
                continue
            if url.startswith("javascript:"):
                continue
            yield response.follow(url)

    def parse_pdf(self, response: Response):
        pdf = parser.from_buffer(response.body, xmlContent=True)

        if isinstance(pdf, tuple):
            return None

        content = pdf["content"]

        if content is None:
            return None

        selector = Selector(text=content)
        texts = selector.xpath("/html/body/node()").getall()
        texts = (BeautifulSoup(text, "lxml").text for text in texts)

        for page, text in enumerate(
            filter(lambda text: len(text) > MIN_CONTENT_LENGTH, texts)
        ):
            if mean_ord(text) > 1000:
                continue

            if len(text) > 1000:
                for part in text.split("\n\n"):
                    if len(part) < MIN_CONTENT_LENGTH:
                        continue

                    if self.add_hash(part):
                        yield {
                            "text": part,
                            "page": page + 1,
                            "url": response.url,
                        }
            else:
                if self.add_hash(text):
                    yield {
                        "text": text,
                        "page": page + 1,
                        "url": response.url,
                    }

    def parse(self, response: Response):
        if response.url.endswith(".pdf"):
            return self.parse_pdf(response)

        if isinstance(response, TextResponse):
            return self.parse_text(response)
