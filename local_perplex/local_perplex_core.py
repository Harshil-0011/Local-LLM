from __future__ import annotations

import math
import re
from collections import Counter, namedtuple
from typing import Iterable
from urllib.parse import urlparse


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+(?:['-][a-zA-Z0-9]+)?")
RankedSource = namedtuple("RankedSource", ["title", "url", "content", "relevance", "category"])


def tokenize(text: str) -> list[str]:
    """Tokenize text in pure Python for ranking and graph extraction."""
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text or "")]


def calculate_score(query: str, content: str) -> float:
    """Calculate a normalized term-frequency relevance score."""
    query_tokens = tokenize(query)
    content_tokens = tokenize(content)
    if not query_tokens or not content_tokens:
        return 0.0

    content_counts = Counter(content_tokens)
    score = 0.0
    for token in set(query_tokens):
        if token in content_counts:
            score += 1.0 + math.log(content_counts[token])

    return min(score / math.log(1.0 + len(content_tokens)), 1.0)


def _category_for_url(url: str) -> str:
    host = (urlparse(url or "").netloc or "").lower()
    if host.endswith(".edu") or "arxiv.org" in host or "scholar.google" in host:
        return "Academic"
    if host.endswith(".gov"):
        return "Government"
    if "github.com" in host or "stackoverflow.com" in host:
        return "Technical"
    if "youtube.com" in host or "youtu.be" in host:
        return "Video"
    if "reddit.com" in host:
        return "Community"
    return "General"


def _source_get(source, key: str, default: str = ""):
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


class ResearchEngine:
    """Pure-Python source ranker with the old native module interface."""

    def rank_sources(self, query: str, sources: Iterable[dict]) -> list[RankedSource]:
        ranked: list[RankedSource] = []
        for source in sources:
            title = _source_get(source, "title", "Unknown")
            url = _source_get(source, "url", "")
            content = _source_get(source, "content", "")
            category = _source_get(source, "category", "") or _category_for_url(url)
            score = calculate_score(query, f"{title}\n{content}")
            if category == "Academic":
                score *= 1.25
            elif category == "Government":
                score *= 1.15
            ranked.append(
                RankedSource(
                    title=title,
                    url=url,
                    content=content,
                    relevance=min(score, 1.0),
                    category=category,
                )
            )

        return sorted(ranked, key=lambda item: item.relevance, reverse=True)
