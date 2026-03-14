---
name: create-custom-prompt
description: >
  Use when asked to create, update, or review a VS Code prompt file (.prompt.md).
  Provides the correct file format, frontmatter fields, and guidelines for
  writing effective, reusable slash-command prompts.
argument-hint: <prompt-name> [task description]
---

# Create a Custom Prompt File

Prompt files (`.prompt.md`) are **slash commands** — reusable, manually-invoked
prompts for common repetitive tasks. They carry structured instructions, context,
and optionally restrict which tools or agent are used.

## When to Use a Prompt (vs other customizations)

| Need | Use |
|---|---|
| Repeatable task invoked manually (`/my-prompt`) | **Prompt file** (`.prompt.md`) |
| Persistent AI persona with tool restrictions | Custom Agent (`.agent.md`) |
| Domain knowledge loaded automatically | Skill (`SKILL.md`) |
| Coding standards always applied | Instructions (`.instructions.md`) |

## File Location

| Scope | Location |
|---|---|
| Workspace (shared with team) | `.github/prompts/<prompt-name>.prompt.md` |
| User profile (personal, all workspaces) | `~/.copilot/prompts/<prompt-name>.prompt.md` |

## File Format

```markdown
---
name: <prompt-name>
description: <Short description of what this prompt does>
argument-hint: <hint shown after /prompt-name in chat input>
agent: ask | agent | plan | <custom-agent-name>   # optional
model: <model-name>                                 # optional
tools:
  - <tool-name>
---

# Prompt Body

Detailed instructions for the task. Use Markdown formatting.

Reference workspace files with relative Markdown links.
Reference tools with `#tool:<tool-name>` syntax.

Use `${input:variableName}` or `${input:variableName:placeholder}` for user inputs.
Use `${selection}` to capture the current editor selection.
```

## Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `name` | No | Name used after `/` in chat. Defaults to file name. |
| `description` | No | Short description shown in the `/` command menu. |
| `argument-hint` | No | Hint text shown after the slash command in chat input. |
| `agent` | No | Agent to use: `ask`, `agent`, `plan`, or a custom agent name. Defaults to current. |
| `model` | No | Specific model. Defaults to user-selected model in picker. |
| `tools` | No | Restricts available tools for this prompt. Prompt tools take highest priority. |

## Tool List Priority

When running a prompt:
1. Tools from the **prompt file** (highest priority)
2. Tools from the **referenced agent** (if `agent:` is set)
3. Default tools for the selected agent

## Built-in Variables

| Variable | Description |
|---|---|
| `${selection}` | Currently selected text in the editor |
| `${input:name}` | Prompts user for input with label `name` |
| `${input:name:placeholder}` | Input with placeholder text |
| `#tool:<tool-name>` | Reference a tool in the body text |

## Step-by-Step Workflow

### Step 1: Define the task
What exactly does this prompt do? It should be a single, well-scoped task (e.g.,
"scaffold a new Android ViewModel", "run and fix unit tests", "prepare PR description").

### Step 2: Choose the right agent
- `ask` → best for research, explanations, no file changes
- `agent` → best for tasks that need file editing or terminal
- `plan` → best for planning tasks
- Custom agent name → when the task requires a specialized persona

### Step 3: Create the file
```
.github/prompts/<prompt-name>.prompt.md
```

### Step 4: Write the body
- Be specific about expected **input** and **output format**.
- Use `${input:variableName}` for required inputs.
- Reference related instruction files instead of duplicating rules.
- Include examples of expected output where helpful.

### Step 5: Verify
- [ ] `name` matches the file name (no spaces, hyphen-separated).
- [ ] The task is scoped to ONE action — not a multi-step workflow (use an agent + handoffs for that).
- [ ] Input variables are clearly named.
- [ ] Tools are minimal and appropriate.
- [ ] Prompt can be invoked with `/prompt-name` and produce useful output independently.

## Examples

### Scaffold Android ViewModel
```markdown
---
name: new-android-viewmodel
description: Scaffold a new Android ViewModel with Hilt injection and StateFlow
argument-hint: <ViewModelName>
agent: agent
tools:
  - create_file
  - read_file
---

Create a new Android ViewModel named `${input:viewModelName:e.g. LoginViewModel}`.

Follow these conventions:
- Use Hilt `@HiltViewModel` + `@Inject constructor`
- Expose UI state via `StateFlow<UiState>`
- Use `viewModelScope` for coroutines

[See project conventions](.github/instructions/android/viewmodel.instructions.md)
```

### Generate Commit Message
```markdown
---
name: commit-msg
description: Generate a Conventional Commits message for the current changes
agent: ask
---

Review the following diff and generate a commit message following Conventional Commits format:

```
${selection}
```

Format:
```
<type>(<scope>): <short description>

[optional body]

[optional footer: TICKET-ID]
```

Types: feat, fix, test, static, refactor, docs, format, chore, perf
```

### Security Review
```markdown
---
name: security-review
description: Review selected code for OWASP Top 10 and memory safety issues
argument-hint: [scope description]
agent: reviewer-security
---

Perform a security review of the code below.

${selection}

Check for:
1. Input validation / injection vulnerabilities
2. Memory safety (buffer overflows, use-after-free)
3. Authentication and authorization issues
4. Hardcoded secrets or credentials
5. OWASP Top 10 violations

End with `[PASS]` or `[FAIL: <findings>]`.
```

## Tips for Effective Prompts

- **One task per prompt** — if it needs multiple agents, use handoffs instead.
- **Reference don't duplicate** — link to instructions files rather than copying rules.
- **Name clearly** — `/new-android-viewmodel` is better than `/create-vm`.
- **Use `argument-hint`** so users know what to type after `/name`.
- **Test with the play button** — open the `.prompt.md` file and press ▶ to iterate fast.

## Prerequisites

- VS Code 1.87+ with the GitHub Copilot extension installed.
- A workspace with a `.github/prompts/` directory (create it if absent).
- Understanding of the task you want to automate as a reusable prompt.


## Troubleshooting

- **AI never auto-loads the skill / agent / instruction** — verify `disable-model-invocation` is not `true` and `description` contains a clear "Use when ..." trigger phrase.
- **Skill / prompt not shown in the `/` command menu** — check that `user-invocable` is not `false` and the file is saved to the correct `.github/` subdirectory.
- **`name` validator error (`FM_NAME_DIR_MISMATCH`)** — the `name` frontmatter field must exactly match the directory/file name (case-sensitive, lowercase, hyphens only).
- **Companion file not found by the AI** — reference files with paths relative to the skill/instruction/prompt file (e.g., `./examples/good.cpp`).


## References
- [VS Code Prompt Files Docs](https://code.visualstudio.com/docs/copilot/customization/prompt-files)
- [Awesome Copilot Prompts](https://github.com/github/awesome-copilot/tree/main/prompts)
