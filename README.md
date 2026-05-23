# Closira AI Customer Support Workflow

Python CLI prototype for the Closira assignment. It demonstrates FAQ answering from an
SOP, lead qualification, escalation detection, escalation logging, and final conversation
summaries.

## Setup

Requires Python 3.10 or newer. There are no required third-party packages.

```bash
python -m closira_agent.cli --demo
```

For an interactive session:

```bash
python -m closira_agent.cli
```

Commands in interactive mode:

- `/lead` starts the structured lead qualification questions.
- `/summary` prints the current structured conversation summary.
- `/quit` exits.

## Optional Gemini Mode

The project includes a stdlib Gemini `generateContent` API adapter. Set an API key only if you
want model-refined wording and model-assisted final summaries:

```bash
$env:GEMINI_API_KEY="your_key_here"
python -m closira_agent.cli --mode gemini --demo
```

Optional model override:

```bash
$env:GEMINI_MODEL="gemini-2.5-flash"
```

Without `GEMINI_API_KEY`, use the default local mode. Local mode is deterministic and is
the safest path for evaluation because every answer is grounded directly in `data/sop.json`.

## Project Structure

- `closira_agent/sop.py`: loads SOP JSON and returns grounded answers.
- `closira_agent/escalation.py`: rule-based escalation detection and JSONL logging.
- `closira_agent/workflow.py`: orchestrates FAQ answering, lead capture, escalation, and summaries.
- `closira_agent/cli.py`: demo and interactive CLI.
- `data/sop.json`: documented SOP source used by the AI.
- `prompt_design.md`: system prompt and design reasoning.
- `test_transcripts/`: scenario transcripts for the required behaviours.

## Trade-Offs

The core prototype intentionally keeps safety logic deterministic. This limits natural
language flexibility, but it makes SOP boundaries, escalation reasons, and test behaviour
clear. Gemini mode is optional and constrained to rewriting approved drafts or summarising
known fields.
"# closira-agent" 
