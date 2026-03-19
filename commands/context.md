---
description: Configure your academic profile (university, discipline, citation style)
allowed-tools: Read, Write, Bash(cat ~/.academic-research/*), Bash(mkdir -p ~/.academic-research/*)
argument-hint: [optional: university name]
---

# Academic Context Setup

Interactively configure your academic profile. This is saved to `~/.academic-research/config.local.md` and used as defaults for all research sessions.

## Questions to ask the user:

1. **Universität / University**: Which university are you at?
2. **Studiengang / Program**: What's your field of study? (e.g., BWL, Informatik, Wirtschaftsinformatik)
3. **Zitationsstil / Citation style**: Default citation style? (apa7, ieee, harvard, mla, chicago)
4. **Sprache / Language**: Preferred output language? (deutsch, english)
5. **HAN-Server**: Do you have institutional database access via HAN-Server? (yes/no)
6. **Bevorzugte Module / Preferred modules**: Any preferred search sources? (e.g., semantic_scholar, econbiz)

## After collecting answers, write the config file:

```markdown
---
name: academic-context
---
## Universität
<answer>

## Studiengang
<answer>

## Zitationsstil
<answer>

## Sprache
<answer>

## HAN-Server
<enabled/disabled>

## Bevorzugte Module
- <module1>
- <module2>
```

Save to: `~/.academic-research/config.local.md`

Confirm:
```
✅ Academic context saved!
File: ~/.academic-research/config.local.md

Your defaults:
  University:  <name>
  Program:     <program>
  Citation:    <style>
  Language:    <language>

These will be used as defaults for /research. Override with inline args.
```
