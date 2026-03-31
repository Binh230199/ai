# Canonical Pattern Synthesis

The final guide should not tell developers to remember dozens of disconnected rules. It should derive a smaller set of canonical coding patterns that satisfy many rules at once.

## Synthesis Principles

- prefer one best default style when several compliant forms exist
- prefer patterns that reduce ambiguity, hidden conversions, and future fix churn
- explain why the canonical form is better than nearby alternatives
- connect each canonical form to the rule families it satisfies

## Required Per Pattern

- the engineering intent
- the preferred default form
- when the form is especially important
- what nearby but inferior forms to avoid
- which rule families benefit from using it consistently

## Quality Bar

The result should make an engineer more likely to write compliant code by default, not merely after a long review checklist.
