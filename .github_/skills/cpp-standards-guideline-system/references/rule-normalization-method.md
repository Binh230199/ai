# Rule Normalization Method

Each rule should become a structured record that supports later synthesis.

## Minimum Fields

- `rule_id`
- `title`
- `family`
- `intent`
- `preferred_pattern`
- `anti_patterns`
- `related_rules`
- `conflict_risk`
- `evidence_location`

## Extraction Principles

- Preserve source identifiers and traceability.
- Rewrite the rule in original language suitable for engineering use.
- Separate what the rule forbids from what the preferred coding pattern should be.
- Capture what else usually breaks when this rule is fixed badly.
- Prefer concise, machine-usable wording over essay-style notes.

## Family Heuristic

Group rules by how a developer experiences them in code, not by document chapter alone. Typical family types include:

- declarations and initialization
- object lifetime and ownership
- type conversions and narrowing
- expressions and side effects
- interfaces and APIs
- control flow and error handling
