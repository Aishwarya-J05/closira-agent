# Closira AI Customer Support Workflow

A Python CLI agent that simulates an AI-powered customer support workflow for small and medium businesses. Built as an AI Engineering internship assignment for **Closira** — an AI customer communication platform.

The agent handles a full customer conversation across four structured stages, grounded strictly in a predefined SOP file. Runs locally with no API key required. Optional Gemini mode available for LLM-powered responses.

---

## What It Does

| Stage | What happens |
|---|---|
| **FAQ Answering** | Answers inbound questions from `data/sop.json` only. Flags and escalates anything outside the SOP. |
| **Lead Qualification** | Collects customer context via 2–3 structured follow-up questions. Triggered with `/lead`. |
| **Escalation Detection** | Detects complaints, medical questions, pricing negotiation, out-of-scope queries, and angry sentiment — logs reason to `logs/escalations.jsonl`. |
| **Conversation Summary** | Generates a structured summary of intent, collected data, SOP gaps, and recommended next action. Triggered with `/summary`. |

Demo business: **Bloom Aesthetics Clinic** — services include Botox (from £200), Fillers (from £250), and free Consultations.

---

## Project Structure

```
assignment/
├── closira_agent/
│   ├── cli.py              # CLI entrypoint and conversation loop
│   ├── sop.py              # SOP loader, keyword matcher, SopRepository class
│   ├── escalation.py       # Escalation rules, detection logic, JSONL logger
│   ├── models.py           # Dataclasses — SopAnswer, ConversationState, etc.
│   └── llm.py              # Optional Gemini API adapter
├── data/
│   └── sop.json            # SOP — the agent's only knowledge source
├── logs/
│   └── escalations.jsonl   # Written at runtime when escalations occur
├── test_transcripts/
│   ├── 01_in_sop_question.md
│   ├── 02_out_of_scope_question.md
│   ├── 03_escalation_trigger.md
│   ├── 04_lead_qualification.md
│   └── 05_conversation_summary.md
├── prompt_design.md
├── requirements.txt
└── README.md
```

---

## Setup

**Requirements:** Python 3.10+

```bash
# 1. Clone the repo
git clone https://github.com/Aishwarya-J05/closira-agent.git
cd closira-agent

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

### Local mode (default — no API key needed)

```bash
python -m closira_agent.cli
```

Answers are matched from `data/sop.json` using keyword scoring. Fully deterministic. Recommended for testing and evaluation.

### Gemini mode (LLM-powered responses)

```bash
# Set your API key first
# Windows
set GEMINI_API_KEY=your_key_here

# Mac/Linux
export GEMINI_API_KEY=your_key_here

# Run with Gemini
python -m closira_agent.cli --mode gemini
```

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## CLI Commands

Once the agent is running, use these commands at any point in the conversation:

| Command | What it does |
|---|---|
| `/lead` | Starts lead qualification — asks 2–3 structured questions |
| `/summary` | Prints a structured summary of the conversation so far |
| `/quit` | Exits the CLI |

Any other input is treated as a customer message.

---

## Example Conversations

**In-SOP question**
```
Customer: what are your botox prices?
AI: Botox treatments start from £200. The price varies depending on the
    number of areas treated. A free consultation is included.
```

**Out-of-scope question**
```
Customer: do you do laser hair removal?
AI: The clinic SOP lists these services: Botox, Fillers, Consultations.
    I do not see that specific treatment listed in the SOP.
[ESCALATED — out_of_scope]
```

**Escalation on complaint**
```
Customer: i was overcharged and nobody replied
AI: I do not have that information in the clinic SOP, so I should connect
    you with a team member who can resolve this directly.
[ESCALATED — complaint_detected]
```

**Lead qualification**
```
Customer: /lead
AI: What type of business or practice are you enquiring on behalf of?
Customer: a beauty salon
AI: Have you had aesthetic treatments before, or would this be your first time?
Customer: first time
AI: Is there a particular treatment in mind, or would you prefer a consultation?
```

**Conversation summary**
```
Customer: /summary
AI: Intent: Enquired about services and pricing.
    Qualification: Beauty salon, first-time enquiry, open to consultation.
    SOP gaps: Laser hair removal not covered.
    Escalated: Yes — out of scope question.
    Next action: Follow up via WhatsApp with service list and consultation booking link.
```

---

## Escalation Triggers

The agent escalates and logs to `logs/escalations.jsonl` when:

- Customer raises a complaint or expresses frustration
- Medical question asked (suitability, allergies, drug interactions)
- Pricing negotiation or discount request detected
- SOP cannot answer the question
- Customer explicitly asks for a human
- Abusive or hostile language detected

---

## Prompt Design

See [`prompt_design.md`](./prompt_design.md) for:

- Full system prompt with design rationale
- Hallucination prevention strategy
- Confidence-based escalation logic
- Tone and persona definition
- Known limitations and trade-offs

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Local mode | Keyword scoring against `data/sop.json` |
| LLM mode | Google Gemini 2.5 Flash (optional) |
| State tracking | `ConversationState` dataclass |
| Escalation logging | Structured JSONL (`logs/escalations.jsonl`) |
| Interface | CLI — no frontend required |

---

## Known Limitations

- No persistent memory across sessions — each run starts fresh
- Local mode uses keyword matching, not semantic similarity — works well for the SOP scope but won't generalise to arbitrary phrasing
- Gemini mode depends on API availability and free-tier rate limits
- Sentiment detection in local mode is rule-based (keyword list) — Gemini mode handles nuance better

---

Built by [Aishwarya Joshi](https://github.com/Aishwarya-J05)
