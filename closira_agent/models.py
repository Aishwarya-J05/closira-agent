from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SopAnswer:
    answer: str
    confidence: float
    matched_topics: list[str] = field(default_factory=list)
    sop_gaps: list[str] = field(default_factory=list)


@dataclass
class EscalationDecision:
    should_escalate: bool
    reasons: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class LeadProfile:
    business_type: str | None = None
    team_size: str | None = None
    current_tools: str | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "business_type": self.business_type,
            "team_size": self.team_size,
            "current_tools": self.current_tools,
            "notes": self.notes,
        }


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConversationState:
    session_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    lead_profile: LeadProfile = field(default_factory=LeadProfile)
    escalations: list[EscalationDecision] = field(default_factory=list)
    sop_gaps: list[str] = field(default_factory=list)
    unanswered_count: int = 0

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(ConversationTurn(role=role, content=content))

    def transcript_text(self) -> str:
        return "\n".join(f"{turn.role}: {turn.content}" for turn in self.turns)
