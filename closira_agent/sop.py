from __future__ import annotations

import json
from pathlib import Path

from .models import SopAnswer


class SopRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.business = self.data["business"]
        self.topics = self.data["topics"]

    def answer(self, customer_message: str) -> SopAnswer:
        message = customer_message.lower()
        matches: list[tuple[str, dict]] = []

        for key, topic in self.topics.items():
            if any(keyword in message for keyword in topic.get("keywords", [])):
                matches.append((key, topic))

        if not matches:
            return SopAnswer(
                answer=(
                    "I do not have that information in the clinic SOP, so I should connect "
                    "you with the team rather than guess."
                ),
                confidence=0.2,
                sop_gaps=[customer_message],
            )

        key, topic = matches[0]
        return SopAnswer(
            answer=topic["answer"],
            confidence=float(topic.get("confidence", 0.9)),
            matched_topics=[key],
        )

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
