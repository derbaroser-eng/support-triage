#!/usr/bin/env python3
"""
test_triage.py — failing tests for support-triage.

Run: python workspace/products/support-triage/test_triage.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "triage.py"

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, detail))


def run_triage(messages: list[dict]) -> dict:
    """Run triage.py with the given messages and return parsed output."""
    payload = json.dumps({"messages": messages})
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return {"error": f"exit={r.returncode}", "stderr": r.stderr[:200]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "stdout": r.stdout[:200]}


# --- test 1: bug classification ---
out = run_triage([{"id": "m1", "text": "The export button is broken since yesterday"}])
check("bug: classified", isinstance(out, list) and len(out) == 1, str(out)[:100])
if isinstance(out, list) and out:
    check("bug: bucket is bug", out[0].get("bucket") == "bug", str(out[0]))
    check("bug: confidence >= 0.7", out[0].get("confidence", 0) >= 0.7, str(out[0]))

# --- test 2: feature_request classification ---
out = run_triage([{"id": "m2", "text": "Would be nice to have dark mode"}])
check("feature: classified", isinstance(out, list) and len(out) == 1, str(out)[:100])
if isinstance(out, list) and out:
    check("feature: bucket is feature_request", out[0].get("bucket") == "feature_request", str(out[0]))

# --- test 3: urgent classification ---
out = run_triage([{"id": "m3", "text": "Security breach! Cannot access account"}])
check("urgent: classified", isinstance(out, list) and len(out) == 1, str(out)[:100])
if isinstance(out, list) and out:
    check("urgent: bucket is urgent", out[0].get("bucket") == "urgent", str(out[0]))

# --- test 4: noise classification ---
out = run_triage([{"id": "m4", "text": "Unsubscribe from this list"}])
check("noise: classified", isinstance(out, list) and len(out) == 1, str(out)[:100])
if isinstance(out, list) and out:
    check("noise: bucket is noise", out[0].get("bucket") == "noise", str(out[0]))

# --- test 5: fallback (no keyword match) ---
out = run_triage([{"id": "m5", "text": "Hello, I have a question about billing"}])
check("fallback: classified", isinstance(out, list) and len(out) == 1, str(out)[:100])
if isinstance(out, list) and out:
    check("fallback: bucket is noise", out[0].get("bucket") == "noise", str(out[0]))
    check("fallback: confidence is 0.3", out[0].get("confidence") == 0.3, str(out[0]))

# --- test 6: invalid input (missing messages key) ---
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input=json.dumps({"foo": "bar"}),
    capture_output=True,
    text=True,
    timeout=10,
)
check("invalid: exit code 1", r.returncode == 1, f"rc={r.returncode}")

# --- test 7: empty messages array ---
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input=json.dumps({"messages": []}),
    capture_output=True,
    text=True,
    timeout=10,
)
check("empty: exit code 1", r.returncode == 1, f"rc={r.returncode}")

# --- test 8: multiple messages ---
out = run_triage([
    {"id": "m6", "text": "Bug in login"},
    {"id": "m7", "text": "Feature request: export to CSV"},
])
check("multi: classified", isinstance(out, list) and len(out) == 2, str(out)[:100])

# --- test 9: no secrets in output ---
out = run_triage([{"id": "m8", "text": "My password is secret123"}])
if isinstance(out, list) and out:
    check("no secrets: password not in output", "secret123" not in json.dumps(out), str(out))

# --- test 10: deterministic (same input → same output) ---
out1 = run_triage([{"id": "m9", "text": "Broken feature"}])
out2 = run_triage([{"id": "m9", "text": "Broken feature"}])
check("deterministic: same output", out1 == out2, f"{out1} vs {out2}")

# --- report ----------------------------------------------------------------
passed = sum(1 for _, ok, _ in results if ok)
failed = [(n, d) for n, ok, d in results if not ok]
print(f"\n{passed}/{len(results)} assertions passed")
if failed:
    print("\nFAILED:")
    for n, d in failed:
        print(f"  {n}  ({d})")
    sys.exit(1)
print("ALL TESTS GREEN")
