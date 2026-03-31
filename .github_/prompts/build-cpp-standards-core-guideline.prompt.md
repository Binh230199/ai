---
name: "build-cpp-standards-core-guideline"
description: "Build a core C++ coding guideline from an AUTOSAR, MISRA, or similar standards PDF by parsing the source, extracting rules, mapping interactions, and synthesizing a final markdown guide."
argument-hint: "Provide standard=<name>; pdf=<file:///...pdf>; output=<cpp-core-autosar.md>; artifacts=<artifacts/cpp-standards-guideline>"
agent: "standards-orchestrator"
---

Build a complete core C++ coding guideline from the provided standards document.

Use the `cpp-standards-guideline-system` skill and follow the full workflow:

1. create or update the manifest and runbook
2. parse the source PDF to text or markdown
3. extract normalized rule records
4. map rule relationships and generate the rule graph
5. synthesize the final core guideline markdown file
6. verify the output contract and artifact chain

The final output should be an original engineering guideline, not a copied or lightly reformatted version of the source document.
