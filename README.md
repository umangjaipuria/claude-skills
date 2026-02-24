# Claude Skills

A collection of skills for [Claude Code](https://claude.ai/product/claude-code) and [Claude Cowork](https://claude.com/product/cowork).

## Available Skills

| Skill | Description |
|---|---|
| [domain-brainstorm](./domain-brainstorm) | Brainstorm brandable domain names and check availability in real time |

## Installing a Skill

Skills are installed by placing them in `~/.claude/skills/` on your machine.

### Option A — Ask Claude to install it

Open Claude Code or Cowork and say:

> Install the domain-brainstorm skill from github.com/umangjaipuria/claude-skills

Claude will handle the rest.

### Option B — Two terminal commands

```bash
git clone https://github.com/umangjaipuria/claude-skills.git
cp -r claude-skills/domain-brainstorm ~/.claude/skills/
```

That's it. The skill will be available the next time you start a Claude session.

## Requirements

Some skills require additional dependencies. Check the skill's own README for details before installing.
