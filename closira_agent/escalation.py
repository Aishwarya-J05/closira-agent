from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from .models import ConversationState, EscalationDecision, SopAnswer


FUZZY_MATCH_THRESHOLD = 0.82
SHORT_WORD_LENGTH = 4

ANGRY_TERMS = {
    "angry",
    "annoyed",
    "awful",
    "bad service",
    "charged",
    "complain",
    "complaint",
    "did not reply",
    "double charged",
    "extra charge",
    "frustrated",
    "furious",
    "ignored",
    "money back",
    "no response",
    "nobody is responding",
    "not responding",
    "not happy",
    "overcharged",
    "refund",
    "ridiculous",
    "terrible",
    "upset",
    "wrong charge",
}

HUMAN_REQUEST_TERMS = {
    "agent",
    "human",
    "manager",
    "person",
    "representative",
    "someone",
    "supervisor",
}

MEDICAL_TERMS = {
    "allergy",
    "diagnose",
    "dosage",
    "infection",
    "medical",
    "pregnant",
    "risk",
    "safe for me",
    "side effect",
}

NEGOTIATION_TERMS = {
    "cheaper",
    "discount",
    "negotiate",
    "price match",
    "reduce the price",
}


class EscalationPolicy:
    def __init__(self, log_path: str | Path = "logs/escalations.jsonl", confidence_threshold: float = 0.55) -> None:
        self.log_path = Path(log_path)
        self.confidence_threshold = confidence_threshold

    def evaluate(self, message: str, sop_answer: SopAnswer, state: ConversationState) -> EscalationDecision:
        lowered = self._normalize(message)
        reasons: list[str] = []

        if sop_answer.confidence < self.confidence_threshold:
            reasons.append("low_confidence_or_out_of_scope")
        if self._contains_keyword(lowered, ANGRY_TERMS):
            reasons.append("angry_sentiment_or_complaint")
        if self._contains_keyword(lowered, HUMAN_REQUEST_TERMS) and self._contains_keyword(
            lowered, {"speak", "talk", "connect", "transfer", "call"}
        ):
            reasons.append("explicit_human_request")
        if self._contains_keyword(lowered, MEDICAL_TERMS):
            reasons.append("medical_question")
        if self._contains_keyword(lowered, NEGOTIATION_TERMS):
            reasons.append("pricing_negotiation")
        if state.unanswered_count > 2:
            reasons.append("more_than_two_unanswered_questions")

        return EscalationDecision(
            should_escalate=bool(reasons),
            reasons=sorted(set(reasons)),
            confidence=sop_answer.confidence,
        )

    def _contains_keyword(self, message: str, keywords: set[str]) -> bool:
        return max(self._phrase_match_score(message, keyword) for keyword in keywords) >= FUZZY_MATCH_THRESHOLD

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

    def log(self, state: ConversationState, decision: EscalationDecision, message: str) -> None:
        if not decision.should_escalate:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": state.session_id,
            "message": message,
            "reasons": decision.reasons,
            "confidence": decision.confidence,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
