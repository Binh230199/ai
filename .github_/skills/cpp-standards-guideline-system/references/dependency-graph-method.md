# Dependency Graph Method

The purpose of the graph is to show which rules reinforce each other and where a local fix can create a new violation.

## Relationship Types

- `reinforces`: following rule A makes rule B easier to satisfy
- `prerequisite`: rule A should usually be addressed before rule B
- `overlap`: rules A and B push toward the same coding pattern
- `conflict-risk`: a naive fix for rule A often triggers rule B
- `fix-order`: rules that should be applied in sequence

## What To Map

- high-leverage canonical idioms
- rules that share a preferred coding form
- rules with common anti-patterns
- frequent fix collisions

## What Not To Map

- trivial cross-references with no practical effect
- vague conceptual similarity without coding impact
