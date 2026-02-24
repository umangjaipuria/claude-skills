---
name: domain-brainstorm
description: Brainstorm brandable domain names and check availability in real time via RDAP. Use this skill when the user asks for domain name suggestions.
allowed-tools: 
   - Bash(python3 *)
   - AskUserQuestion
---

Brainstorm domain names for the user and check availability as you go.

## What makes a good domain name

**Length**: 1–2 syllables strongly preferred. 3 syllables acceptable. Avoid longer.

**Exceptions to length**: The only exception to the length requirement is if the name itself is shorter, but to find an available domain name you need to add prepositions or verbs like 'to', 'with', 'get', etc. 

**Sound**: Easy to say aloud and spell from hearing it. No ambiguous spellings (e.g. avoid "ph" vs "f" confusion). Passes the "radio test" — someone hears it once and can find it.

**Character**: Distinctive and ownable. Evokes something without being literal. Not a generic dictionary compound (e.g. "SmartWrite" is bad). Single evocative words are better than compounds.

**Feel**: Match the product's tone. Energetic words (Bolt, Surge) for fast tools. Calm words (Drift, Flow) for focus tools. Warm words (Bloom, Glow) for consumer apps.

**Memorable**: Should be easy to recognize and recall, which means familiar words for the target audience or shifts in spelling that immediately feel natural (e.g. 'wispr' for 'whisper')


**Avoid**:
- Hyphens, numbers, or unusual spellings
- Words that are trademarked by major tech companies (don't suggest "Slack" even if slack.com is free)
- Names of well-known existing products or services in adjacent spaces
- Overused startup suffixes (-ly, -ify, -io as a word)
- Anything that sounds clinical, corporate, or generic

**Categories that work well**: single verbs, nature words, materials, motion words, light/sound words, short abstract nouns, coined two-syllable words, words borrowed from other languages (Latin, Japanese, etc.).

**Explore based on TLD popularity**: TLDs like .com and .app are very popular, and most common words would already be taken. To converge on a suitable name quickly, explore a broader set  ideas, longer words, more esoteric words, minor spelling modifications (skirting the principle above) to find an available name. We can be more picky when it comes to less prime .TLDs. 

**Suggest TLDs:** If domains in the user's preferred TLD are not available, suggest other popular TLDs relevant to the user's product / website.

## Workflow

1. **Gather user's stated preferences:** Ask the user for context about their product / website, intended audience and preferences on direction. Ask them if they want the name to be close to the product and its goal or have some signicance (ask what kind of significance) or if it can be completely unrelated. Ask if they have a preference for TLD.

2. **Gather user's revealed preferences:** Generate 10-15 candidates and, without checking for availability, ask the user which they like and dislike directionally. This is only for direction, not final suggestions, and will reveal what they actually prefer.

3. **Brainstorm:** With the above context (and prioritizing revealed preferences over statedpreferences), generate 40-50 candidate names. Spread across multiple categories — don't cluster in one area. Before suggesting, do a quick sanity check: would any name collide with a well-known product, brand, or service?

2. **Check availability** by running the script (see below). Check all candidates in one batch. Note: with rate limiting, 25 names x 2 TLDs takes about 30 seconds. Warn the user that this may take a while.

3. **Report results**:
   - List each **available** domain with a one-line note on why it works for this product.
   - If there are errors, mention them briefly.
   - If nothing good is available, say so honestly.

4. **Iterate** if the user wants more. Keep track of names already checked — never re-suggest them. To find new territory, try:
   - Different etymology: Latin roots, Japanese words, nautical terms, musical terms
   - Coined/invented words: combine short syllables into new words (e.g. Kova, Zumo, Nyla)
   - Different emotional register: playful vs serious, warm vs sharp
   - Adjacent metaphors: if "light" words are taken, try "sound" or "motion" words

## Running the script

The script is at scripts/domain-checks.py. First verify it exists, and if not, tell the user it's missing and where to place it.

```bash
python3 domain-checks.py -t <tld> [-t <tld> ...] -n Name1,Name2,Name3,...
```

- Available domains are printed to **stdout**, one bare domain per line.
- Errors go to **stderr**.
- Unavailable domains produce no output.

Keep batches under 100 names. If checking multiple TLDs, they are all handled in one run.
