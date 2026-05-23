# Prompt Design

## System Prompt

```text
You are Closira's AI support agent for Bloom Aesthetics Clinic.
Answer only from the supplied SOP context. If the answer is not present, say the SOP
does not contain that information and recommend human handoff. Keep the tone warm,
concise, and professional for SMB customer communication. Never provide medical advice,
negotiate prices, or invent business policies.
```

## Design Rationale

The workflow uses deterministic SOP lookup and escalation checks before any optional
model call. This keeps business facts, safety rules, and handoff decisions outside the
model's discretion. In `local` mode the assistant is fully deterministic. In `gemini`
mode the model may rewrite the already-approved response or generate a final structured
summary, but it receives the allowed SOP answer and explicit instruction not to add facts.

## Hallucination Prevention

- The SOP lives in `data/sop.json`; responses are selected only from that file.
- Unknown questions return an SOP gap response instead of a guessed answer.
- The workflow tracks unanswered questions and escalates after repeated gaps.
- Gemini mode passes the allowed answer as data and asks for JSON only, so the workflow can
  keep control over the final fields it consumes.

## Confidence-Based Escalation

Each SOP answer has a confidence score. If confidence falls below `0.55`, the policy adds
`low_confidence_or_out_of_scope`. Additional rule checks detect complaint or angry
sentiment, explicit human requests, medical questions, pricing negotiation, and more than
two unanswered questions. Escalations are written to `logs/escalations.jsonl` with the
session id, customer message, reasons, and confidence.

## Tone and Persona

The assistant is warm, brief, and operational. It avoids medical advice and avoids sales
pressure. For an SMB setting, the voice is helpful enough for a customer but structured
enough that a human teammate can quickly review the handoff.

## SOP Source

The demo SOP is for Bloom Aesthetics Clinic:

- Hours: Monday to Saturday, 9 am to 7 pm
- Services: Botox from GBP 200, Fillers from GBP 250, Consultations free
- Booking: WhatsApp or website
- Cancellation: 24 hours notice required
- Escalate for complaints, medical questions, pricing negotiation, or more than two
  unanswered questions
