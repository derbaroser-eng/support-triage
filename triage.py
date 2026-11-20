#!/usr/bin/env python3
"""
triage.py — deterministic support message classifier.

Reads JSON from stdin, writes JSON to stdout.
No external calls, no file I/O, no secrets in output.
"""
import json
import sys
import re

KEYWORDS = {
    "urgent": ["security", "breach", "down", "outage", "cannot access", "data loss"],
    "bug": ["broken", "not working", "error", "crash", "fails", "bug", "glitch"],
    "feature_request": ["would be nice", "can you add", "feature", "wish", "suggestion"],
    "noise": ["unsubscribe", "spam", "promo", "marketing"],
}

PRIORITY = ["urgent", "bug", "feature_request", "noise"]


def classify(text: str) -> dict:
    text_lower = text.lower()
    for bucket in PRIORITY:
        for kw in KEYWORDS[bucket]:
            if kw in text_lower:
                # Whole-word match = 0.9, substring = 0.7
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_lower):
                    return {"bucket": bucket, "confidence": 0.9}
                return {"bucket": bucket, "confidence": 0.7}
    return {"bucket": "noise", "confidence": 0.3}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("error: invalid JSON", file=sys.stderr)
        return 1

    if "messages" not in data:
        print("error: missing 'messages' key", file=sys.stderr)
        return 1

    messages = data["messages"]
    if not isinstance(messages, list) or len(messages) == 0:
        print("error: messages must be a non-empty array", file=sys.stderr)
        return 1

    results = []
    for msg in messages:
        if not isinstance(msg, dict) or "id" not in msg or "text" not in msg:
            print("error: each message must have 'id' and 'text'", file=sys.stderr)
            return 1
        if not isinstance(msg["text"], str):
            print("error: 'text' must be a string", file=sys.stderr)
            return 1

        result = classify(msg["text"])
        results.append({
            "id": msg["id"],
            "bucket": result["bucket"],
            "confidence": result["confidence"],
            "summary": f"Classified as {result['bucket']}",
        })

    json.dump(results, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
