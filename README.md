# Closira AI Customer Support Workflow

A Python CLI prototype of an AI-powered customer support agent for small and medium businesses. Built as part of an AI Engineering internship assignment for **Closira** — an AI customer communication platform.

The agent handles a simulated end-to-end customer conversation across four structured stages, using **Google Gemini** as the LLM and a predefined **SOP (Standard Operating Procedure)** as its only knowledge source.

---

## What It Does

The agent works through four stages in sequence:

| Stage | What happens |
|---|---|
| **FAQ Answering** | Answers inbound questions grounded strictly in `data/sop.json`. Will not hallucinate or infer beyond the SOP. |
| **Lead Qualification** | Asks 2–3 structured questions to understand the customer's context and intent. |
| **Escalation Detection** | Detects complaints, medical questions, pricing negotiation, anger, or out-of-scope queries — flags and logs the reason. |
| **Conversation Summary** | Generates a structured internal summary: customer intent, collected data, SOP gaps, and recommended next action. |

The demo business is **Bloom Aesthetics Clinic** — a fictional aesthetics clinic offering Botox, fillers, and free consultations.

---

## Project Structure

```
closira-agent/
├── main.py                    # CLI entrypoint and conversation loop
├── agent/
│   ├── conversation.py        # ConversationState dataclass + stage machine
│   ├── stages.py              # Per-stage orchestration logic
│   ├── llm.py                 # Gemini API wrapper
│   └── prompts.py             # All prompts with design rationale
├── data/
│   └── sop.json               # SOP — the agent's only knowledge source
├── logs/                      # Escalation logs written here at runtime
├── test_transcripts/
│   ├── 01_in_sop_question.md
│   ├── 02_out_of_scope_question.md
│   ├── 03_escalation_trigger.md
│   ├── 04_lead_qualification.md
│   └── 05_conversation_summary.md
├── prompt_design.md           # Prompt decisions, hallucination prevention, escalation logic
├── requirements.txt
└── .env.example
```

---

## Setup

**Requirements:** Python 3.11+, a Google Gemini API key ([get one free](https://aistudio.google.com/apikey))

```bash
git clone https://github.com/Aishwarya-J05/closira-agent.git
cd closira-agent

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file:

```
GEMINI_API_KEY=your_key_here
```

Run the agent:

```bash
python main.py
```

---

## Example Conversations

**In-SOP question**
```
You: what are your botox prices?
Aria: Our Botox treatments start from £200. The exact price depends on the
      number of areas treated, and a free consultation is always included
      so you can discuss your goals with one of our practitioners.
```

**Out-of-scope question**
```
You: do you do laser hair removal?
Aria: That is a great question, but I am afraid laser hair removal is not
      something we currently offer based on the information I have. I would
      not want to give you inaccurate details — I can connect you with a
      member of the team via WhatsApp who can confirm exactly what is available.
[ESCALATED — reason: out_of_scope | triggered_by: model]
```

**Escalation on complaint**
```
You: this is ridiculous, I was double charged and nobody is responding
Aria: I am really sorry to hear that — that sounds incredibly frustrating,
      and it is absolutely not the experience we want you to have. I am
      flagging this for a member of our team right now so someone can look
      into this personally.
[ESCALATED — reason: customer_complaint_detected | triggered_by: rule]
```

---

## Escalation Triggers

The agent escalates (flags for human handoff) when any of these are detected:

- Customer raises a complaint or expresses frustration
- Medical question asked (suitability, allergies, drug interactions)
- Pricing negotiation or discount request
- SOP cannot answer the question after two exchanges
- Customer explicitly asks for a human
- Abusive or hostile language detected

Escalation events are logged to `logs/escalations.jsonl` with timestamp, stage, reason, and trigger source.

---

## Design Decisions

See [`prompt_design.md`](./prompt_design.md) for the full breakdown of:

- System prompt design and rationale
- Hallucination prevention strategy
- Confidence-based escalation
- Tone and persona definition
- Known limitations and trade-offs

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Backend | Python 3.11, modular `agent/` package |
| State management | Custom `ConversationState` dataclass + stage enum |
| Knowledge source | `data/sop.json` — injected into system prompt |
| Interface | CLI (no frontend required) |
| Logging | Structured JSONL escalation log |

---

## Known Limitations

- **No persistent memory across sessions** — each CLI run starts a fresh conversation. Trivially fixable with a session store.
- **Single SOP source** — the agent only knows what is in `sop.json`. Gaps are handled by escalation, not inference.
- **Gemini rate limits** — free tier has RPM limits. The LLM wrapper includes basic retry logic but not exponential backoff.
- **Sentiment detection is LLM-delegated** — the model flags angry sentiment via its JSON output. A secondary rule-based check on keywords provides defence-in-depth but is not exhaustive.

---

Built by [Aishwarya Joshi](https://github.com/Aishwarya-J05)
