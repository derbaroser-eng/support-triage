# SPEC — Support Message → Product Work Triage

## What it does

Reads raw support messages (email body, chat transcript, form submission) and
classifies each into exactly one bucket:

| bucket | meaning |
|---|---|
| `bug` | Something is broken; a user cannot complete a task |
| `feature_request` | User asks for a capability that does not exist |
| `urgent` | Revenue or security impact; needs human attention now |
| `noise` | Spam, duplicate, or not actionable |

Outputs a JSON array of `{id, bucket, confidence, summary}` ready for a product
ticketing system.

## What it does NOT do

- Does not send email, create tickets, or modify any external system
- Does not use an LLM for classification (deterministic rules only)
- Does not store raw message content (only the classification result)

## Input

```json
{"messages": [{"id": "msg-001", "text": "The export button is broken since yesterday"}]}
```

## Output

```json
[{"id": "msg-001", "bucket": "bug", "confidence": 0.92, "summary": "Export button broken"}]
```

## Exit codes

- `0` — success, all messages classified
- `1` — invalid input (missing `messages` key, empty array, or non-string text)
- `2` — classification failed (no rule matched and no fallback)

## Rules (deterministic, no ML)

1. **urgent** — contains any of: `security`, `breach`, `down`, `outage`, `cannot access`, `data loss`
2. **bug** — contains any of: `broken`, `not working`, `error`, `crash`, `fails`, `bug`, `glitch`
3. **feature_request** — contains any of: `would be nice`, `can you add`, `feature`, `wish`, `suggestion`
4. **noise** — contains any of: `unsubscribe`, `spam`, `promo`, `marketing`
5. **fallback** — if no rule matches, classify as `noise` with confidence 0.3

## Confidence scoring

- Exact keyword match: 0.9
- Partial match (keyword is substring): 0.7
- Fallback: 0.3

## Constraints

- No external API calls
- No file I/O beyond reading stdin and writing stdout
- No secrets in output
- Deterministic: same input → same output
