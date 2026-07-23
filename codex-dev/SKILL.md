---
name: codex-dev
description: "Route implementation work to Codex CLI; Claude specs, reviews, verifies. Use when a task is a work order — implementation from a settled spec, refactors, mechanical migrations, bug fixes with a known repro, test writing, CI fixes, dependency bumps, or bulk codebase exploration."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# Codex Development

Claude Code sessions only. Codex/other harnesses: skip; never self-delegate.

Rationale: Claude (Fable/Opus) tokens metered + expensive; Codex flat-rate. GPT-5.6+ is usually the better and faster model at writing/implementing code; Claude wins at ergonomics — judgment, design, spec-writing, review, orchestration. So Codex types, Claude thinks and verifies.

## Route

Delegate to Codex (default for hands-on work):

- implementation from a frozen spec; refactors; mechanical migrations
- bug fixes with known repro; test writing; coverage fills
- CI fixes, dependency bumps, scripts/tooling
- bulk codebase exploration where raw reading ≫ the answer

Keep in Claude:

- design, API design, architecture, naming, UX judgment
- tasks where writing the spec IS the work (ambiguity = design)
- tiny edits (~<20 lines, single obvious change) — delegation overhead loses
- anything needing session tools: MCP (browser/computer-use/pencil), 1Password, secrets
- destructive/irreversible ops, releases, pushes, GitHub mutations — Claude-side per git rules
- review of Codex output — never delegated, never skipped

Mixed task: Claude designs first, freezes spec, delegates build-out.
Heuristic: prompt reads as a work order → delegate; writing it forces decisions → design, Claude.

## Invoke

Separate Bash/Write tool calls; don't chain them into one command.

**Step 1 — write the prompt with the Write tool** to your scratchpad directory as `codex-<task>.txt`.
Not `mktemp` + heredoc: that sidesteps macOS `mktemp` template quirks, shell quoting, and the
permission prompts `$(...)` draws (same reason codex-code-review splits its steps).

**Step 2 — run Codex in the background.** Set `run_in_background: true` on this Bash call.

```bash
codex exec \
  -m gpt-5.6-sol \
  -c 'model_reasoning_effort="high"' \
  -s workspace-write \
  -C <repo> \
  -o <scratch>/codex-<task>.out.md \
  - < <scratch>/codex-<task>.txt \
  2> <scratch>/codex-<task>.err.log
```

**Step 3 — validate the run before you believe it. Exit 0 does not mean success.** A Codex whose
command runner failed to start still exits 0 and writes a confident, plausible-sounding failure
report into `-o`. Run all three checks; none of them is exit status:

```bash
grep -c ERROR <scratch>/codex-<task>.err.log   # authoritative: must print 0
git -C <repo> status -sb                       # ground truth: files Codex claims must appear
wc -c < <scratch>/codex-<task>.out.md          # weak: 0 bytes means it died early
```

stderr is authoritative — it's the only channel that reports a failed run. `git status` is ground
truth: if Codex says it changed `foo.py` and `foo.py` isn't dirty, nothing happened. A non-empty
`-o` proves nothing; a broken run fills it with prose.

(`grep -c` exits 1 when the count is 0; that's the good case, not a command failure.)

If an `ERROR` names `code-mode host`, the install is broken, not the task: `gpt-5.6-*` routes shell
commands through a `codex-code-mode-host` binary that must sit beside `codex`. Some packagings omit
it — the Homebrew cask ships only `codex` itself. Reinstall via `https://chatgpt.com/codex/install.sh`,
which installs both and verifies the pair. Whatever that run reported is fiction; re-run it.

**Step 4 — read the `-o` file, only after the completion notification.** Don't parse the JSONL
stream; don't poll; don't act on partial output.

**Critical — background, always.** Implementation runs routinely exceed 10 minutes. Foreground Bash
times out at 2 minutes and hands you partial output that reads like a finished result. Tell the user
Codex is running and you'll report back. Don't kill quiet runs under 30 minutes.

**Critical — stdin.** `- < file` feeds the prompt on stdin and closes it. Never invoke without a
stdin redirect; a background Codex with an open stdin blocks forever.

**Critical — keep stderr.** Redirect to a file, don't `2>/dev/null`. It carries the opening banner
(model, sandbox, effort) plus every `ERROR` line — which, per Step 3, is the *only* place a failed
run announces itself. Discarding stderr is how you end up reporting a fabricated success. It's a
file, not context: `grep` it, don't read it whole. On non-zero exit, read it, report to the user, and
don't retry — auth or config needs a human.

Flags:

- `-m gpt-5.6-sol` — pinned deliberately. Without it you inherit `~/.codex/config.toml`, which the
  Codex desktop app rewrites when you switch models. Pinned = reproducible.
- `-c 'model_reasoning_effort="high"'` — also pinned; otherwise config.toml governs. Ladder:
  `medium` mechanical, `high` default, `xhigh` gnarly bugs, `max` last resort. Skip `ultra` — it
  auto-delegates subtasks, which fights a scoped hand-off.
- `-s workspace-write` — Codex edits the repo and runs commands/tests freely. `codex exec` is already
  `approval: never`, so this needs no approval plumbing. Network is **off**: if the task installs
  deps, add `-c sandbox_workspace_write.network_access=true`.
- `-C <repo>` — working root. Outside a git repo also pass `--skip-git-repo-check`.
- `-o <file>` — final message. Unique per run; parallel tasks in separate repos need separate files.
- Don't add `--ephemeral` (codex-code-review uses it) — it skips session persistence, which kills
  `resume` below.

`--yolo` (hidden alias for `--dangerously-bypass-approvals-and-sandbox`) disables the sandbox and
allows writes anywhere on disk. Claude Code's auto-mode classifier denies it absent an explicit
`Bash(codex exec:*)` permission rule. `-s workspace-write` covers the real use case; don't reach for
yolo.

Follow-up fixes — cheaper than fresh runs, keeps context. `resume` takes `-m`/`-o`/`-c` but has no
`-C` and no `-s`, so `cd` into the repo and set the sandbox via `-c`:

```bash
(cd <repo> && codex exec resume --last \
  -m gpt-5.6-sol \
  -c 'model_reasoning_effort="high"' \
  -c 'sandbox_mode="workspace-write"' \
  -o <scratch>/codex-<task>.fix.out.md \
  - < <scratch>/codex-<task>.fix.txt \
  2> <scratch>/codex-<task>.fix.err.log)
```

Step 3's validation applies to `resume` too.

## Prompt contract

Codex starts with zero session context. Every prompt: goal, exact repo/paths, constraints, non-goals,
proof expected (exact test command), output shape ("report files changed + test output"). Spec quality
decides success.

## Verify (Claude, always)

- `git status -sb` + read the full diff; judge like a contributor PR
- run focused tests yourself or demand proof output; Codex claims are advisory
- iterate via `resume`; after 2 failed rounds, take over and do it directly
- before ship, second-opinion the diff via the `codex-code-review` skill

## Economics

Win = generation + exploration tokens moved to Codex; Claude spends only on spec + diff review. Don't
ping-pong trivia through delegation; don't re-read what Codex already summarized.
