"""Knowledge base service for FAQ-backed answers."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.database import FaqEntry

logger = logging.getLogger(__name__)


@dataclass
class FaqMatch:
    """Represents a FAQ match for a query."""

    entry: FaqEntry
    score: float


class FaqService:
    """Service for retrieving FAQ answers from the SQL knowledge base."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def find_best_match(self, query: str, *, threshold: float = 0.55) -> Optional[FaqMatch]:
        """Return the best FAQ entry for the provided query.

        The lookup uses a light-weight fuzzy matching heuristic so we can serve
        answers even without external LLM calls.
        """

        cleaned_query = query.strip()
        if not cleaned_query:
            return None

        async with self._lock:
            async with get_async_session() as session:
                entries = await self._fetch_active_entries(session)

        if not entries:
            return None

        keywords = _extract_keywords(cleaned_query)
        best_match: Optional[FaqMatch] = None
        for entry in entries:
            score = _calculate_match_score(cleaned_query, keywords, entry)
            if best_match is None or score > best_match.score:
                best_match = FaqMatch(entry=entry, score=score)

        if best_match and best_match.score >= threshold:
            logger.debug("FAQ match found for query '%s' with score %.2f", cleaned_query, best_match.score)
            return best_match

        logger.debug("No FAQ match met the threshold for query '%s'", cleaned_query)
        return None

    async def _fetch_active_entries(self, session: AsyncSession) -> List[FaqEntry]:
        """Fetch all active FAQ entries."""

        result = await session.execute(
            select(FaqEntry).where(FaqEntry.is_active.is_(True))
        )
        return list(result.scalars().all())


def _extract_keywords(text: str) -> List[str]:
    """Extract significant keywords from a query."""

    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    keywords = [token for token in tokens if len(token) > 2]
    return keywords[:8] if keywords else [text.lower()]


def _calculate_match_score(query: str, keywords: List[str], entry: FaqEntry) -> float:
    """Calculate a heuristic similarity score between the query and an entry."""

    question = entry.question.lower()
    answer = entry.answer.lower()
    tags = " ".join(entry.tags or []).lower()

    question_similarity = SequenceMatcher(None, query.lower(), question).ratio()
    answer_similarity = SequenceMatcher(None, query.lower(), answer).ratio() * 0.5

    keyword_hits = sum(1 for kw in keywords if kw in question or kw in tags)
    keyword_score = min(keyword_hits / max(len(keywords), 1), 1.0)

    combined_score = (question_similarity * 0.6) + (answer_similarity * 0.2) + (keyword_score * 0.2)

    if entry.category:
        category_bonus = 0.05 if any(entry.category.value in kw for kw in keywords) else 0.0
    else:
        category_bonus = 0.0

    return min(combined_score + category_bonus, 1.0)


faq_service = FaqService()
