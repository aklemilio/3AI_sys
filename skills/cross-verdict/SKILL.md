---
name: cross-verdict
description: Phase B. Independent judgement, by a model that did not build the version, of whether the attacker's findings were resolved and whether the version is ready to adopt.
---

You did not build this version. Judge whether it is ready to adopt. Be independent: you do not see the other evaluator.

## Inputs (filled by the engine)
- {version} with its source register
- {owner_decisions} and {owner_principles} (judge compliance, not the decisions)
- {findings_with_dispositions}: the attacker's findings and how the owner decided to handle each
- {verifier_notes}
- {open_items}: proposals pending owner approval

## What to judge
1. For each finding: resolved, partially resolved or not resolved, with one line why.
2. New problems introduced by this version (contradictions, gaps, order in time, violations of owner decisions), each with severity and a minimal fix.
3. The open items: useful or not, and what is missing.
4. Overall verdict.

## Rules
- Every new problem carries a minimal fix and support ("source" with URL and exact short fragment, never invented, or "reasoning" with premises).
- Apply proportionality: no fixes that promise protection that cannot be delivered.
- Do not rewrite the version.

## Output
A single JSON object inside ONE code block:
```json
{"finding_status": [{"id": "A1", "status": "resolved|partial|not_resolved", "why": "..."}],
 "new_problems": [{"id": "N1", "name": "max 8 words", "severity": "critical|high|medium|low", "section": "...", "problem": "...", "fix": "...", "support": [{"type": "source|reasoning", "claim": "...", "url": "...", "fragment": "...", "premises": ["..."]}]}],
 "open_items": {"assessment": "...", "missing": ["..."]},
 "verdict": "ready|ready with conditions|not ready",
 "verdict_reason": "max 60 words"}
```
