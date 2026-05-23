from __future__ import annotations

import argparse
import json

from .workflow import CustomerSupportWorkflow


DEMO_MESSAGES = [
    "What are your Botox prices?",
    "Can I book on WhatsApp?",
]


def run_demo(workflow: CustomerSupportWorkflow) -> None:
    state = workflow.new_state()
    print("Closira demo session\n")
    for message in DEMO_MESSAGES:
        print(f"Customer: {message}")
        print(f"AI: {workflow.respond(state, message)}\n")

    lead_intent = "I run a small salon and want this for my own enquiries."
    print(f"Customer: {lead_intent}")
    first_question = workflow.respond(state, lead_intent)
    print(f"AI: {first_question}")
    first_answer = "A beauty salon"
    print(f"Customer: {first_answer}\n")
    workflow.capture_lead_answer(state, first_answer)

    while question := workflow.next_lead_question(state):
        print(f"AI: {question}")
        sample_answer = {
            "Roughly how many people are on your team?": "6 people",
            "What tools do you currently use for customer enquiries?": "WhatsApp Business and Instagram DMs",
        }[question]
        print(f"Customer: {sample_answer}\n")
        workflow.capture_lead_answer(state, sample_answer)

    print("Lead summary:")
    print(json.dumps(workflow.lead_summary(state), indent=2))
    print("\nConversation summary:")
    print(json.dumps(workflow.conversation_summary(state), indent=2))


def run_interactive(workflow: CustomerSupportWorkflow) -> None:
    state = workflow.new_state()
    print("Closira support workflow. Type /lead for qualification, /summary to finish, or /quit.")
    while True:
        message = input("Customer: ").strip()
        if message in {"/quit", "quit", "exit"}:
            break
        if message == "/summary":
            print(json.dumps(workflow.conversation_summary(state), indent=2))
            continue
        if message == "/lead":
            while question := workflow.next_lead_question(state):
                answer = input(f"AI: {question}\nCustomer: ").strip()
                workflow.capture_lead_answer(state, answer)
            print(json.dumps(workflow.lead_summary(state), indent=2))
            continue
        print(f"AI: {workflow.respond(state, message)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Closira AI customer support workflow")
    parser.add_argument("--sop", default="data/sop.json", help="Path to SOP JSON")
    parser.add_argument("--mode", choices=["local", "gemini"], default="local", help="Use local rules or Gemini for response polishing and summaries")
    parser.add_argument("--demo", action="store_true", help="Run a scripted demo conversation")
    args = parser.parse_args()

    workflow = CustomerSupportWorkflow(sop_path=args.sop, mode=args.mode)
    if args.demo:
        run_demo(workflow)
    else:
        run_interactive(workflow)


if __name__ == "__main__":
    main()
