# Delivery Contract

An agentic-system design produced by this factory should normally contain all of the sections below.

## Required Sections

### 1. Design Brief

- objective
- scope
- assumptions
- constraints
- integrations
- exit criteria

### 2. Architecture

- system layers
- execution flow
- recovery flow
- parallelism strategy

### 3. Agent Matrix

- agent name
- role
- inputs
- outputs
- tools
- hard boundaries

### 4. Copilot Customization Bundle

- `copilot-instructions.md` strategy
- file-specific instructions
- prompt entrypoints
- custom agents
- skills
- hooks

### 5. Runtime Artifacts

- manifests
- ledgers
- runbooks
- result reports
- verification artifacts

### 6. Verification and Recovery

- validation rules
- verifier responsibilities
- retry handling
- resume handling
- completion proof

### 7. Optimization Strategy

- token reduction tactics
- latency reduction tactics
- context partitioning

### 8. Rollout Plan

- implementation order
- validation order
- operational risks
- team adoption notes

## Optional File Tree Output

When asked to package the system, include a concrete file tree such as:

```text
.github/
  copilot-instructions.md
  instructions/
  agents/
  prompts/
  hooks/
  skills/
artifacts/
  <system-name>/
```
