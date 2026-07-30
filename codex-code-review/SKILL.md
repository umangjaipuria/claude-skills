---
name: codex-code-review
description: Get a second-opinion code review from OpenAI Codex CLI (GPT-5.6-Sol xhigh). Use when the user asks for a code review, wants a second pair of eyes, or you want to validate significant changes.
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - AskUserQuestion
---

Get an independent code review from OpenAI's Codex CLI using GPT-5.6-Sol at extra-high reasoning effort. Codex acts as a principal engineer providing a second opinion. You have more context than Codex — use your own judgment to decide what feedback to incorporate.

## Invoking Codex

Use `codex exec` to run a one-shot review. Always write output to a temp file for reliable capture.

**Important:** Each step below must be a separate Bash tool call. Do NOT use `$()` command substitution or combine steps into one command — this triggers permission prompts.

**Step 1 — Create a temp file:**
```bash
mktemp /tmp/codex-review.XXXXXXXX
```
This prints the created file path. Save this path for use in steps 2 and 3.

**Step 2 — Run Codex in the background** (use the literal path printed by step 1):
```bash
codex exec \
  -m gpt-5.6-sol \
  -c 'model_reasoning_effort="xhigh"' \
  --ephemeral \
  -s read-only \
  -o <TMPFILE> \
  "$PROMPT" < /dev/null
```

**Critical — close stdin:** The `< /dev/null` redirect is required. Without it, codex may block waiting for stdin input when run as a background job, and the task will hang indefinitely instead of completing.

**Critical — run in background:** You MUST set `run_in_background: true` on this Bash tool call. Codex with xhigh reasoning regularly takes 3-8 minutes. If you run it in the foreground, the Bash tool will time out after 2 minutes and return partial/empty output — you will then incorrectly interpret incomplete results as the final review. Running in the background ensures you receive an explicit completion notification. Do NOT read the temp file, check on progress, or take any action on the review until you receive the background completion notification. Tell the user that Codex is running and you'll report back when it finishes.

**Step 3 — Read and clean up (only after background completion):**
After receiving the background task completion notification, use the Read tool to read the temp file, then delete it with `rm <TMPFILE>`.

In steps 2 and 3, replace `<TMPFILE>` with the actual path printed by step 1.

**Flags explained:**
- `-m gpt-5.6-sol` — model selection (always use this for reviews). Pinned, so a `/model` switch in the Codex app can't silently change what runs.
- `-c 'model_reasoning_effort="xhigh"'` — deep thinking, principal-engineer level. Sol also accepts `max` and `ultra` above this; `xhigh` is the sweet spot for review latency. Avoid `ultra` — it auto-delegates subtasks.
- `--ephemeral` — no conversation persistence, clean context
- `-s read-only` — read-only sandbox, prevents Codex from modifying any files
- `-o <TMPFILE>` — write output to file (avoids noisy stdout metadata)

### Optional invocation choices

Keep these out of the default command. Follow each option's conditions before using it.

#### Faster service tier

Add this flag to an initial or resumed invocation only when the user explicitly asks for the fast
service tier or faster Codex execution:

```bash
-c 'service_tier="fast"'
```

The fast service tier is more expensive. Do not enable it by default or infer that the user wants it
from urgency, task complexity, or a general request to finish quickly.

#### Continue the review session

Use a persisted session when the calling agent expects another round of feedback or iteration:

1. Omit `--ephemeral` from the initial invocation. This is required; ephemeral sessions cannot be
   resumed.
2. After assessing or applying the first review, create a new temp output file with the Step 1
   `mktemp` command.
3. Run the follow-up in the background from the same repository:

```bash
codex exec resume --last \
  -m gpt-5.6-sol \
  -c 'model_reasoning_effort="xhigh"' \
  -c 'sandbox_mode="read-only"' \
  -o <NEW_TMPFILE> \
  "$FOLLOWUP_PROMPT" < /dev/null
```

`--last` selects the newest persisted session for the current working directory. If the session ID
is known or multiple Codex runs may overlap, replace `--last` with the exact session ID. Apply the
same background-run, completion-notification, output-reading, cleanup, and error-handling rules to
every resumed round. Add `-c 'service_tier="fast"'` only if the user explicitly requested the more
expensive fast tier.

**Critical — temp file creation:** On macOS, `mktemp` only replaces the X's when they are the **last characters** of the template. Do NOT add a file extension (e.g., `.md`) after the X's — this causes `mktemp` to use the template literally without substitution. The template `/tmp/codex-review.XXXXXXXX` (no extension) is correct and must be used verbatim.

**Error handling:** If codex returns a non-zero exit code, read stderr for the error message. Report the error to the user and do not retry automatically — there may be an auth or config issue the user needs to resolve.

## Telling Codex what to review

Codex has shell access — it can run git commands and read files itself. Don't bloat the prompt by embedding diffs or file contents. Instead, tell Codex *what* to do in the prompt and let it retrieve the code.

### Git diff (most common — review uncommitted changes)
Tell Codex to run `git diff` (or `git diff --cached` for staged changes).

### Git commit(s)
Tell Codex the commit hash(es) and to run `git show <hash>` or `git log -p <hash1>..<hash2>`.

### Specific files or directory
Tell Codex the file paths or directory to review and to read them itself.

### Scoping the review
To narrow what Codex reviews, pass the scope in the prompt itself. For example:
- "Run `git diff -- src/api/routes.py src/api/middleware.py` and review those changes"
- "Read the files in `src/auth/` and review them"
- "Run `git show abc1234 -- lib/` and review only the lib changes"

Codex handles the filtering — no need to embed content.

### Important:
- Always tell Codex it can run git commands if it needs more context beyond what you asked it to review.
- Always tell Codex to return an error message (not silently fail) if it cannot access something.

## Constructing the prompt

The prompt to Codex must include these sections:

### 1. Context summary (required)
A brief summary of what the code changes are for and the goal. This prevents Codex from optimizing for the wrong thing.

### 2. What to review (required)
Tell Codex what to review — a git command to run, file paths to read, or (rarely) embedded code.

### 3. Focus areas (optional but recommended)
If you or the user have specific concerns, list them. Examples: "pay special attention to error handling", "check for SQL injection", "verify the caching logic is correct".

### 4. Output format instructions (required)
Tell Codex exactly how to structure its response:

```
Return your review as plain text in this format:

CRITICAL ISSUES
Issues that must be fixed — bugs, security vulnerabilities, data loss risks.
List each with: file, line/section, issue description, and what should change.
If none, write "None found."

IMPROVEMENTS
Code quality, performance, readability, or maintainability suggestions.
Tag each with a severity: [high] (real impact on correctness, performance, or security if left), [medium] (meaningful quality improvement), [low] (nitpick or style preference).
List each with: severity tag, file, line/section, what to improve, and why.

Be token-efficient. Use whichever is most concise: a brief description, a function/variable name, a short code snippet, or a one-liner fix. Don't rewrite large blocks of code — describe the change instead.

POSITIVE NOTES
Things done well that should be kept.

SUMMARY
2-3 sentence overall assessment.

Do NOT include metadata, conversation artifacts, or commentary outside this format.
If you cannot access a file or run a command, say so clearly in your response instead of silently skipping it.
```

### Example full prompt

```
You are reviewing code changes in a git repository. Here is the context:

**Goal:** Adding rate limiting middleware to the Express API to prevent abuse of the /api/search endpoint.

**Focus areas:** Check that the rate limit configuration is correct, that the middleware ordering is right, and that error responses follow our existing API format.

You have access to git and the filesystem. If you need more context, run git commands to explore. If you cannot access something, say so clearly.

**What to review:** Run `git diff` to see the uncommitted changes, then review them.

Return your review as plain text in this format:
[... format instructions from above ...]
```

## Processing Codex's response

### 1. Read and assess the feedback yourself
Do NOT blindly apply Codex's suggestions. You have far more context about:
- The broader codebase and its conventions
- The user's intent and constraints
- What has already been tried or discussed
- Project-specific patterns and trade-offs

For each piece of feedback, decide:
- **Incorporate** — the feedback is correct and valuable
- **Adapt** — the spirit is right but the specific suggestion needs adjustment for this codebase
- **Discard** — the feedback is wrong, irrelevant, or conflicts with known constraints

### 2. Fix what you can
If Codex identified real issues that you agree with and can fix, fix them before reporting to the user. Don't make the user do work you can handle.

### 3. Report to the user
Present a clear summary structured as:

**Codex Review Summary:**
- Brief overview of what Codex found

**My Assessment:**
- Which feedback points you're incorporating and why
- Which you're discarding and why
- Any points you're unsure about and want the user's input on

**Changes Made:**
- What you fixed based on the review
- Why those changes improve the code

**For Your Decision:**
- Any feedback points that require the user's judgment (e.g., architectural trade-offs, business logic questions)

### 4. If Codex returns errors
If Codex couldn't complete the review (auth issues, timeout, can't access files):
- Report the error clearly to the user
- Do NOT retry automatically
- Suggest what the user might check (codex auth, file permissions, etc.)

## What NOT to do

- Do not treat Codex's feedback as authoritative. It is a second pair of eyes, not the final word.
- Do not call Codex repeatedly in a loop trying to get different answers.
- Do not send the entire repository — keep reviews focused on the relevant changes.
- Do not skip your own assessment. The user is relying on your judgment to filter and contextualize Codex's raw feedback.
