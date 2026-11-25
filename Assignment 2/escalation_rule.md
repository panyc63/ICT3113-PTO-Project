# Proposed category-based cascade — Group P2-11

**Draft for team approval.** The team chooses the pair and both settings using only odd source rows from the frozen tuning set. Use the exact Assignment 1 prompt and category schema for every call. Both models stay resident on the unchanged Assignment 1 CPU-only machine.

1. Classify each ticket with the smaller model.
2. If its valid predicted category belongs to the setting's acceptance list, accept it. The true category is never available to the rule.
3. Otherwise classify the same narrative with the larger model and use that answer. A malformed small-model category also escalates. Transport failures/timeouts are reported as errors rather than silently replaced by an answer.
4. Store exactly one final result and keep the public POST response unchanged. Log the initial prediction, escalation flag and reason, per-model durations, model identities and final answer.

**Selected pair:** [TEAM TO COMPLETE]

| Setting | Accepted predicted categories (pipe-separated) | Evidence/rationale from tuning only |
|---|---|---|
| 1 — conservative | [TEAM TO COMPLETE] | [TEAM TO COMPLETE] |
| 2 — aggressive | [TEAM TO COMPLETE] | [TEAM TO COMPLETE] |

Explain false acceptances of incorrect predictions in the accepted categories, including the observed support and precision: [TEAM TO COMPLETE]

Record the memory-residency evidence file(s) and how these two settings differ: [TEAM TO COMPLETE]

Freeze and commit the final rule before held-out evaluation. Do not choose a different list after inspecting the even-row scores.
