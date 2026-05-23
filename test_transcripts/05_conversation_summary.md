# Conversation Summary

Customer: What are your Botox prices?

AI: Botox starts from GBP 200 at Bloom Aesthetics Clinic.

Customer: Can I book on WhatsApp?

AI: You can book via WhatsApp or through the website.

Customer: I run a small salon and want this for my own enquiries.

AI: What type of business are you enquiring for?

Customer: A beauty salon.

AI: Roughly how many people are on your team?

Customer: 6 people.

AI: What tools do you currently use for customer enquiries?

Customer: WhatsApp Business and Instagram DMs.

Structured summary:

```json
{
  "customer_intent": "service pricing enquiry",
  "key_details_collected": {
    "business_type": "A beauty salon.",
    "team_size": "6 people.",
    "current_tools": "WhatsApp Business and Instagram DMs.",
    "notes": []
  },
  "sop_gaps_identified": [],
  "escalation_reasons": [],
  "recommended_next_action": "Send booking link or WhatsApp follow-up according to SOP."
}
```

Expected result: The final output gives intent, collected details, SOP gaps, escalation
reasons, and a recommended next action.
