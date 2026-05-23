from __future__ import annotations

import re
import uuid
from difflib import SequenceMatcher

from .escalation import EscalationPolicy
from .llm import GeminiClient
from .models import ConversationState
from .sop import SopRepository


FUZZY_MATCH_THRESHOLD = 0.82
SHORT_WORD_LENGTH = 4

LEAD_QUESTIONS = [
    ("business_type", "What type of business are you enquiring for?"),
    ("team_size", "Roughly how many people are on your team?"),
    ("current_tools", "What tools do you currently use for customer enquiries?"),
]

LEAD_INTENT_TERMS = {
    "business",
    "clinic",
    "customer enquiries",
    "demo",
    "my own",
    "salon",
    "team",
    "tools",
}

ACKNOWLEDGEMENT_TERMS = {
    "ok",
    "okay",
    "thanks",
    "thank you",
    "thx",
}

CLOSING_TERMS = {
    "bye",
    "goodbye",
    "got it",
    "no thanks",
    "that helps",
}

GREETING_TERMS = {
    "good afternoon",
    "good evening",
    "good morning",
    "hello",
    "hey",
    "hi",
    "hiya",
}


class CustomerSupportWorkflow:
    def __init__(
        self,
        sop_path: str = "data/sop.json",
        mode: str = "local",
        escalation_log_path: str = "logs/escalations.jsonl",
    ) -> None:
        self.sop = SopRepository(sop_path)
        self.policy = EscalationPolicy(escalation_log_path)
        self.mode = mode
        self.llm = GeminiClient()

    def new_state(self) -> ConversationState:
        return ConversationState(session_id=str(uuid.uuid4()))

    def respond(self, state: ConversationState, customer_message: str) -> str:
        state.add_turn("customer", customer_message)

        if self._looks_like_acknowledgement(customer_message):
            state.unanswered_count = 0
            response = "You are welcome. Let me know if you need anything else."
            state.add_turn("assistant", response)
            return response

        if self._looks_like_greeting(customer_message):
            state.unanswered_count = 0
            response = "Hello. How can I help you with Bloom Aesthetics Clinic today?"
            state.add_turn("assistant", response)
            return response

        if self._looks_like_lead_intent(customer_message):
            question = self.next_lead_question(state)
            response = question or "Thanks, I have the lead qualification details captured."
            state.add_turn("assistant", response)
            return response

        sop_answer = self.sop.answer(customer_message)
        if sop_answer.sop_gaps:
            state.unanswered_count += 1
            state.sop_gaps.extend(sop_answer.sop_gaps)
        else:
            state.unanswered_count = 0

        decision = self.policy.evaluate(customer_message, sop_answer, state)
        if decision.should_escalate:
            state.escalations.append(decision)
            self.policy.log(state, decision, customer_message)
            response = self._escalation_response(sop_answer.answer, decision.reasons)
        else:
            response = sop_answer.answer

        if self.mode == "gemini" and self.llm.available:
            drafted = self.llm.complete_json(
                "Rewrite the assistant response for a customer. Do not add facts. Preserve escalation status and reason.",
                {
                    "customer_message": customer_message,
                    "allowed_sop_answer": sop_answer.answer,
                    "draft_response": response,
                    "should_escalate": decision.should_escalate,
                    "escalation_reasons": decision.reasons,
                },
            )
            response = drafted.get("response", response)

        state.add_turn("assistant", response)
        return response

    def next_lead_question(self, state: ConversationState) -> str | None:
        for field_name, question in LEAD_QUESTIONS:
            if getattr(state.lead_profile, field_name) is None:
                return question
        return None

    def capture_lead_answer(self, state: ConversationState, answer: str) -> None:
        for field_name, _question in LEAD_QUESTIONS:
            if getattr(state.lead_profile, field_name) is None:
                setattr(state.lead_profile, field_name, answer.strip())
                return
        state.lead_profile.notes.append(answer.strip())

    def lead_summary(self, state: ConversationState) -> dict:
        return {
            "qualified": all(getattr(state.lead_profile, field) for field, _ in LEAD_QUESTIONS),
            "profile": state.lead_profile.as_dict(),
        }

    def conversation_summary(self, state: ConversationState) -> dict:
        base = {
            "session_id": state.session_id,
            "customer_intent": self._infer_intent(state),
            "key_details_collected": state.lead_profile.as_dict(),
            "sop_gaps_identified": sorted(set(state.sop_gaps)),
            "escalation_reasons": sorted({reason for item in state.escalations for reason in item.reasons}),
            "recommended_next_action": self._next_action(state),
        }

        if self.mode == "gemini" and self.llm.available:
            return self.llm.complete_json(
                "Create a concise structured handoff summary using only the provided transcript and extracted fields.",
                {"summary_draft": base, "transcript": state.transcript_text(), "sop": self.sop.source_summary()},
            )
        return base

    def _infer_intent(self, state: ConversationState) -> str:
        text = state.transcript_text().lower()
        if "book" in text or "appointment" in text:
            return "booking enquiry"
        if "price" in text or "cost" in text or "botox" in text or "filler" in text:
            return "service pricing enquiry"
        if state.lead_profile.business_type:
            return "lead qualification"
        return "general clinic enquiry"

    def _next_action(self, state: ConversationState) -> str:
        if state.escalations:
            return "Human agent should review the escalation log and contact the customer."
        if not self.lead_summary(state)["qualified"]:
            return "Continue lead qualification by asking the remaining structured questions."
        return "Send booking link or WhatsApp follow-up according to SOP."

    def _escalation_response(self, sop_answer: str, reasons: list[str]) -> str:
        if "pricing_negotiation" in reasons:
            return (
                "I cannot apply discounts or negotiate pricing in chat. "
                "I am handing this to a human agent now. Reason: pricing_negotiation."
            )
        if "medical_question" in reasons:
            return (
                "I cannot answer medical questions in chat. "
                "I am handing this to a human agent now. Reason: medical_question."
            )
        if "angry_sentiment_or_complaint" in reasons:
            return (
                "I am sorry this has been frustrating. "
                "I am handing this to a human agent now. Reason: angry_sentiment_or_complaint."
            )
        if "explicit_human_request" in reasons:
            return "I am handing this to a human agent now. Reason: explicit_human_request."
        return (
            f"{sop_answer} I am handing this to a human agent now. "
            f"Reason: {', '.join(reasons)}."
        )

    def _looks_like_lead_intent(self, message: str) -> bool:
        lowered = self._normalize(message)
        return self._contains_keyword(lowered, LEAD_INTENT_TERMS) and not self._contains_keyword(
            lowered, {"price", "cost", "book", "cancel", "open", "hours", "medical", "complain"}
        )

    def _looks_like_acknowledgement(self, message: str) -> bool:
        lowered = self._normalize(message)
        if not lowered:
            return True
        terms = ACKNOWLEDGEMENT_TERMS | CLOSING_TERMS
        return lowered in terms or self._contains_keyword(lowered, terms)

    def _looks_like_greeting(self, message: str) -> bool:
        lowered = self._normalize(message)
        return self._contains_keyword(lowered, GREETING_TERMS)

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
