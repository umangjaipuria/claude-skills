---
name: fable-orchestrator
description: To be used *ONLY* when a user explicitly asks for this skill by name. This skill tells Claude how to act as an orchestrator for large builds when Claude is running Fable as its LLM. Do not use unless explicitly asked.  
---

# Fable Orchestrator

**Invocation — explicit only.** Run this skill only when the user asks for it by name: `/fable-orchestrator`, "use the fable-orchestrator skill", or equally direct wording. Never load it on your own initiative because a task looks like a fit. If a task seems like it would benefit and the user hasn't asked, say so in one line and let them decide.

All tools are available to this skill.

## When to use

* Only when the user has explicitly asked for this skill by name
* Claude is using Fable as the underlying LLM. Return an error to the user if the underlying model is something else
* The task at hand is a large coding project 

## When not to use

* When user has not asked for this skill explicitly
* When Claude is not running Fable as the underlying model
* When the task at hand is a small feature

## Procedure

You are running Fable, the most expensive and sophisticated model. Your tokens buy judgment, not typing. Your job is to Plan, Delegate, Review, Decide — and to Verify.

Never write implementation code yourself, and never delegate verification. These are the same principle, not a contradiction. What costs real tokens is generating and exploring — writing the code, reading half the repo to find where it goes — and all of that goes to a delegate. Running a linter, a typecheck, a build, or a test suite costs almost nothing and is the only way to know whether a delegate's report is true, so it stays with you.

Delegate tasks as follows:
* use the /codex-dev skill to delegate coding tasks to Codex
* use a sub-agent using Opus to delegate all frontend development (tell it to use the /frontend-design:frontend-design skill) and when judgement calls are required
* use /codex-code-review to have Codex code review all code written by Claude/Opus, and a sub-agent using Opus to review all code written by Codex
* you decide what feedback from code reviews is to be incorporated and what is to be discarded
* for incorporating code review feedback, go back to the implementer. If the implementer was Codex, you can resume the appropriate session as described in the /codex-dev skill
* use /codex-dev using the 5.6 Sol model and "medium" reasoning effort to delegate any online research tasks. Research needs the network flags from codex-dev's "Online research and network access" section — without them Codex answers from memory and sounds just as confident
* if a task can't be delegated successfully — repeated failed rounds, or no delegate fits — stop and ask the user whether to try a different approach or have you do it directly. Do not quietly take over: codex-dev's "after 2 failed rounds, take over and do it directly" rule does not apply here. Spending Fable's tokens on implementation is the user's call, not yours
* when reviewing and verifying coding work, use any lint, compile, typecheck tools available, and run appropriate tests yourself instead of taking the worker at its word
* For large batches of work, especially code that touches on authentication or security or privacy, run adversarial reviews using /codex-code-dev and / or Opus sub-agents (both, if appropriate)