from __future__ import annotations

import json
from pathlib import Path

from .models import ConversationState, EscalationDecision, SopAnswer


ANGRY_TERMS = {
    "angry",
    "annoyed",
    "awful",
    "bad service",
    "complain",
    "complaint",
    "frustrated",
    "furious",
    "not happy",
    "terrible",
    "upset",
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
        lowered = message.lower()
        reasons: list[str] = []

        if sop_answer.confidence < self.confidence_threshold:
            reasons.append("low_confidence_or_out_of_scope")
        if any(term in lowered for term in ANGRY_TERMS):
            reasons.append("angry_sentiment_or_complaint")
        if any(term in lowered for term in HUMAN_REQUEST_TERMS) and any(
            phrase in lowered for phrase in ["speak", "talk", "connect", "transfer", "call"]
        ):
            reasons.append("explicit_human_request")
        if any(term in lowered for term in MEDICAL_TERMS):
            reasons.append("medical_question")
        if any(term in lowered for term in NEGOTIATION_TERMS):
            reasons.append("pricing_negotiation")
        if state.unanswered_count > 2:
            reasons.append("more_than_two_unanswered_questions")

        return EscalationDecision(
            should_escalate=bool(reasons),
            reasons=sorted(set(reasons)),
            confidence=sop_answer.confidence,
        )

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
