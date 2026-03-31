---
name: cpp-standards-guideline-system
description: 'Parse AUTOSAR, MISRA, and similar C++ standards documents, extract rule records, map rule interactions, and synthesize a core guideline with canonical coding patterns and fix-order guidance.'
argument-hint: 'Describe the standard, source PDF path, output filename, artifact root, and any project-specific coding preferences'
user-invocable: true
---

# C++ Standards Guideline System

Use this skill to turn a rule-heavy C++ standards document into a practical core guideline that engineers can follow consistently.

## What This Skill Produces

- a manifest and runbook
- a parsed source artifact
- normalized rule records
- a rule relationship artifact
- a Mermaid rule graph
- a final core guideline markdown file
- a verification report

## When To Use

- building a core coding guideline from AUTOSAR or MISRA C++ source material
- analyzing a standards PDF to derive preferred canonical coding forms
- mapping where coding rules reinforce or interfere with each other
- generating a practical coding guide that reduces multi-rule violations

## Procedure

1. Use the [requirements template](./assets/requirements-template.md) to normalize the job.
2. Create the initial manifest using [manifest-template.json](./assets/manifest-template.json).
3. Install parser dependencies from `./scripts/requirements.txt` if needed.
4. Parse the PDF using [parse_guideline_pdf.py](./scripts/parse_guideline_pdf.py).
5. Extract normalized rule records using the [rule normalization method](./references/rule-normalization-method.md).
6. Map rule interactions using the [dependency graph method](./references/dependency-graph-method.md).
7. Generate the rule graph with [build_rule_graph.py](./scripts/build_rule_graph.py).
8. Synthesize the final guide using the [final guideline template](./assets/final-guideline-template.md).
9. Validate the result against the [output contract](./references/output-contract.md).

## Required Runtime Artifacts

- `artifacts/cpp-standards-guideline/manifest.json`
- `artifacts/cpp-standards-guideline/runbook.md`
- `artifacts/cpp-standards-guideline/source-markdown.md` or `source-text.txt`
- `artifacts/cpp-standards-guideline/rules-normalized.json`
- `artifacts/cpp-standards-guideline/rule-relationships.json`
- `artifacts/cpp-standards-guideline/rule-graph.mmd`
- `artifacts/cpp-standards-guideline/verification-report.md`

## References

- [Workflow](./references/workflow.md)
- [Rule normalization method](./references/rule-normalization-method.md)
- [Dependency graph method](./references/dependency-graph-method.md)
- [Canonical pattern synthesis](./references/canonical-pattern-synthesis.md)
- [Output contract](./references/output-contract.md)
- [Copyright-safe synthesis](./references/copyright-safe-synthesis.md)

## Templates and Schemas

- [Requirements template](./assets/requirements-template.md)
- [Manifest template](./assets/manifest-template.json)
- [Runbook template](./assets/runbook-template.md)
- [Rule record schema](./assets/rule-record-schema.json)
- [Relationship schema](./assets/relationship-schema.json)
- [Final guideline template](./assets/final-guideline-template.md)
