from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote


SYSTEM_PROMPT = """You are Closira's AI support agent for Bloom Aesthetics Clinic.
Answer only from the supplied SOP context. If the answer is not present, say the SOP
does not contain that information and recommend human handoff. Keep the tone warm,
concise, and professional for SMB customer communication. Never provide medical advice,
negotiate prices, or invent business policies."""


class GeminiClient:
    """Tiny stdlib client for the Gemini generateContent API.

    The workflow can run without this client; it is used only when GEMINI_API_KEY is set
    and the CLI is called with --mode gemini.
    """

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete_json(self, instruction: str, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")

        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"{instruction}\n\nReturn JSON only.\n\n{json.dumps(payload)}",
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        model = quote(self.model, safe="")
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API request failed: {detail}") from exc

        chunks: list[str] = []
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    chunks.append(part["text"])
        text = "".join(chunks).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
