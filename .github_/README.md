# C++ Standards Guideline Synthesis System

This folder is intentionally named `.github_` so it can be copied into another repository without immediately activating the Copilot customizations in this workspace.

## Activation

1. Copy this folder into the target repository.
2. Rename `.github_` to `.github`.
3. Ensure Python 3.10+ is available.
4. Install the parser dependencies:

```bash
python -m pip install -r .github/skills/cpp-standards-guideline-system/scripts/requirements.txt
```

5. Validate the copied bundle:

```bash
node .github/hooks/scripts/validate_bundle.mjs
```

## What This System Does

This Copilot bundle turns a standards document such as an AUTOSAR or MISRA C++ PDF into:

- parsed source text or markdown
- a structured rule manifest
- normalized rule records
- a rule interaction graph
- a synthesized core coding guideline file such as `cpp-core-autosar.md`

The system is designed to produce original, paraphrased guidance rather than copying the standard text verbatim.

## Runtime Artifacts

The default runtime artifact root is:

```text
artifacts/cpp-standards-guideline/
```

The system will normally create or update:

- `manifest.json`
- `runbook.md`
- `source-markdown.md` or `source-text.txt`
- `rules-normalized.json`
- `rule-relationships.json`
- `rule-graph.mmd`
- `verification-report.md`

## Prompt Entrypoint

Use the Copilot prompt:

```text
/build-cpp-standards-core-guideline
```

Example input:

```text
standard=AUTOSAR C++14
pdf=file:///C:/Users/binhh/Downloads/AUTOSAR_RS_CPP14Guidelines.pdf
output=cpp-core-autosar.md
artifacts=artifacts/cpp-standards-guideline
```

## Expected Final Output

The system should only consider the job complete when it has produced:

- the parsed source artifact
- normalized rule records
- the rule interaction graph
- the final core guideline markdown file
- a verification report confirming the output contract

## Validation Note

In this repository the folder is intentionally named `.github_`, so VS Code does not treat these agents and prompts as active Copilot customizations yet. Use the bundled validator script to validate the package before copying it. After renaming the folder to `.github` in the target repository, Copilot will resolve the custom agents normally.

