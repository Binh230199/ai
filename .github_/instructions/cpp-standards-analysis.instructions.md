---
description: "Use when analyzing AUTOSAR, MISRA, or similar C++ standards documents, parsing rule corpora, normalizing rule records, deriving core coding idioms, or mapping interactions between coding rules."
---

# C++ Standards Analysis Rules

- Normalize every rule into a structured record before attempting final synthesis.
- Distinguish rule text, rule intent, recommended coding behavior, and downstream side effects.
- Track whether a rule reinforces, overlaps with, or conflicts with another rule.
- Prioritize canonical coding idioms that satisfy several rules at once.
- When a rule has multiple compliant spellings, prefer the form that minimizes collisions with adjacent rules.
- Record fix-order dependencies explicitly.
- Do not produce a shallow list of rule summaries as the final result.

## Minimum Fields Per Normalized Rule

- rule identifier
- short paraphrased title
- rule family
- intent
- preferred pattern
- anti-patterns
- related rules
- conflict-risk notes
- source evidence location
