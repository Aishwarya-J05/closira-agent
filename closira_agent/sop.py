from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from .models import SopAnswer


FUZZY_MATCH_THRESHOLD = 0.82
SHORT_WORD_LENGTH = 4

SERVICE_AVAILABILITY_TERMS = {
    "available",
    "do you do",
    "do you have",
    "offer",
    "provide",
    "service",
    "treatment",
}


class SopRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.business = self.data["business"]
        self.topics = self.data["topics"]

    def answer(self, customer_message: str) -> SopAnswer:
        message = self._normalize(customer_message)
        matches: list[tuple[float, str, dict]] = []

        for key, topic in self.topics.items():
            score = self._topic_match_score(message, topic.get("keywords", []))
            if score >= FUZZY_MATCH_THRESHOLD:
                matches.append((score, key, topic))

        if not matches:
            if self._looks_like_service_availability_question(message):
                service_names = ", ".join(service["name"] for service in self.business["services"])
                return SopAnswer(
                    answer=(
                        f"The clinic SOP lists these services: {service_names}. "
                        "I do not see that specific treatment listed in the SOP."
                    ),
                    confidence=0.75,
                )

            return SopAnswer(
                answer=(
                    "I do not have that information in the clinic SOP, so I should connect "
                    "you with the team rather than guess."
                ),
                confidence=0.2,
                sop_gaps=[customer_message],
            )

        score, key, topic = max(matches, key=lambda match: match[0])
        base_confidence = float(topic.get("confidence", 0.9))
        return SopAnswer(
            answer=topic["answer"],
            confidence=min(base_confidence, score),
            matched_topics=[key],
        )

    def _looks_like_service_availability_question(self, message: str) -> bool:
        return self._keyword_match_score(message, SERVICE_AVAILABILITY_TERMS) >= FUZZY_MATCH_THRESHOLD

    def _topic_match_score(self, message: str, keywords: list[str]) -> float:
        return self._keyword_match_score(message, keywords)

    def _keyword_match_score(self, message: str, keywords: list[str] | set[str]) -> float:
        if not keywords:
            return 0.0
        return max(self._phrase_match_score(message, keyword) for keyword in keywords)

    def _phrase_match_score(self, message: str, keyword: str) -> float:
        keyword = self._normalize(keyword)
        if not keyword:
            return 0.0
        if f" {keyword} " in f" {message} ":
            return 1.0

        keyword_tokens = keyword.split()
        message_tokens = message.split()
        if not keyword_tokens or not message_tokens:
            return 0.0

        if len(keyword_tokens) == 1:
            keyword_token = keyword_tokens[0]
            if len(keyword_token) <= SHORT_WORD_LENGTH:
                return 0.0
            return max(SequenceMatcher(None, keyword_token, token).ratio() for token in message_tokens)

        window_size = len(keyword_tokens)
        if len(message_tokens) < window_size:
            return SequenceMatcher(None, keyword, message).ratio()

        keyword_phrase = " ".join(keyword_tokens)
        return max(
            SequenceMatcher(None, keyword_phrase, " ".join(message_tokens[index : index + window_size])).ratio()
            for index in range(len(message_tokens) - window_size + 1)
        )

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()

    def source_summary(self) -> str:
        lines = [
            f"Business: {self.business['name']}",
            f"Hours: {self.business['hours']}",
            "Services:",
        ]
        for service in self.business["services"]:
            lines.append(f"- {service['name']}: {service['price']}")
        lines.extend(
            [
                f"Booking: {self.business['booking']}",
                f"Cancellation: {self.business['cancellation_policy']}",
                "Escalate if: " + ", ".join(self.business["escalate_if"]),
            ]
        )
        return "\n".join(lines)
