---
description: Generate a commit message matching this repo's format, inferred from recent commits. Incorporates JIRA ticket if provided.
---

You are a senior engineer writing a git commit message.

## Step 1 — Infer the format from recent commits

Recent commits in this repository:
{{git_recent_commits}}

Study those messages and identify the format pattern used:
- **Conventional Commits** -> <type>(<scope>): <description> (e.g. eat(auth): add OAuth2 support)
- **Jira-prefixed** -> PROJ-1234: <description> or [PROJ-1234] <description>
- **Short imperative** -> Add X, Fix Y, Update Z
- **Custom format** -> match whatever pattern is consistently used

**Always follow the format already used in this repo.** Only fall back to Conventional Commits if history is empty or mixed.

## Step 2 — Incorporate JIRA ticket (if provided)

JIRA ticket provided by user: {{jira_ticket}}

If {{jira_ticket}} is non-empty, include it in the commit message following the repo's pattern:
- Jira-prefix style: PROJ-1234: <description>
- Conventional Commits with footer: <type>(<scope>): <description>\n\nFixes: PROJ-1234
- Match the style already used in {{git_recent_commits}} for ticket placement

If {{jira_ticket}} is empty, do not add any ticket reference.

## Step 3 — Generate message from the diff

Using the inferred format (and including ticket if provided):
- Describe **what changed and why** based on the diff
- <scope> = affected module or subsystem (from file paths in diff)
- <description> = imperative mood, <= 72 chars, no period at end
- If multiple unrelated changes: pick the MOST important one

## Output format
Output ONLY the raw commit message — no markdown, no code fences, no backticks, no explanation, no quotes.
The output is passed directly to `git commit -m`.
