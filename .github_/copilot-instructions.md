# C++ Standards Guideline Synthesis

This workspace bundle is designed to turn C++ rule standards such as AUTOSAR or MISRA into a high-leverage core coding guideline.

## Operating Model

- Treat each request as a multi-stage analysis and synthesis workflow, not a single writing task.
- Always create and maintain runtime artifacts under `artifacts/cpp-standards-guideline/` unless the user specifies another artifact root.
- Separate ingestion, rule extraction, dependency mapping, synthesis, and verification.
- Use specialist subagents instead of a single overloaded worker.
- Write all deliverables in English.

## Completion Contract

Do not declare the job complete unless all of the following exist and are internally consistent:

- the parsed document artifact
- the normalized rule set
- the rule relationship graph
- the final guideline markdown file
- a verification report

## Synthesis Rules

- Do not merely enumerate rules one by one.
- Build core rule families that absorb and satisfy multiple related rules.
- Prefer canonical code patterns that minimize future violations across several rules at once.
- Record where fixing one rule can trigger another rule.
- Include fix-order guidance when rule interactions matter.

## Copyright-Safe Output Rules

- Do not reproduce long verbatim passages from copyrighted standards.
- Produce original, paraphrased guidance.
- Cite rule identifiers, titles, and relationships where needed, but do not copy extended rule text.

## Final File Expectations

The final output file such as `cpp-core-autosar.md` should explain:

- the source and scope
- the core rule families
- the preferred canonical patterns
- anti-patterns to avoid
- the rule interaction map
- the recommended fix order and review checklist
