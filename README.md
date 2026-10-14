# coding_skills

If left to their own devices AI agents can create notoriously poor quality code.  They default to creating quick-and dirty rather than well architected code.

This repo has skill that instruct agents to follow good architectural practices.

## What is a capability manifest?

A capability manifest is a small JSON file at the repo root that bundles a set
of skills into a named, configurable unit -- a capability you can hand to a
project. Each manifest names itself (the filename), carries a one-line
description, and lists what it brings with it:

- `skills` -- the `SKILL.md` files that make up the bundle;
- `tools` -- optional helper packages (with their entry files) that enforce
  the skills mechanically.

Configure a project with one manifest and the agent takes on that bundle of
guidance. The same skill may appear in several manifests, so a project can
pick the narrowest bundle that fits.

## Capability manifests

### `python.json` -- best-practices for python development in large codebases

**When would you use this:** On a Python project -- especially a large,
long-lived codebase -- where you want the full stack: the language-neutral
design rules (modularity, concurrency), their Python expression (typing and
value shapes), Python naming, and the lazy-solution philosophy. This is also
the only manifest that ships enforcement tools (the `toolkit/python` checkers),
so choose it when you want machine-checkable rules alongside the judgement
ones.

### `modularity.json` -- language-neutral principles of software modularity

**When would you use this:** For non-Python or polyglot codebases where you
want the architectural rules -- module boundaries, ownership of facts, values
and errors, testing, service/protocol interfaces, concurrency design -- but
none of the Python-specific typing or naming rules. Also a sensible baseline
while a project's language is still undecided.

### `ponytail.json` -- making software as simple and maintainable as possible

**When would you use this:** When you want simplicity discipline on its own
terms -- any language, any size -- just the lazy-senior-dev principles (force
the laziest solution that actually works) without the fuller modularity and
concurrency rule sets. The minimal manifest.
