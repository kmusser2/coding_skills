---
name: review-plan
description: >
  Reviewing a plan: judging a proposed solution against the requirements it
  claims to satisfy and the project's binding rules -- is the problem clear, is
  the root cause confirmed, does it respect the project's modularity, is the
  impact radius minimal, is existing functionality duplicated? Language-agnostic.
license: MIT
compatibility: Language-agnostic
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Reviewing a plan

**Version:** 0.1 (draft).
**Status:** Normative. Maintained at the level of the harness and binding on
the project it is configured for, unless the user explicitly excludes this
skill, or a named statement in it, in that project's AGENTS.md. Silence is
not an exclusion.
**Scope:** the reviewer's job when reviewing a plan -- focus, exploration, and
criteria.
**Contract:** the requirements, plus the project's binding rules.
**Protocol:** you honor `review-independence`, which owns independence, the frozen
contract, the partner objective, the findings, and who decides. This skill owns
only your focus, exploration, and criteria.

## Focus

Reviewing a plan asks whether this is the *right work, done the right way*,
before the cost of building it is paid. It is where the expensive errors are
caught: the wrong problem, the guessed cause, the change that reaches too far,
the functionality that already exists.

You did not write the plan, and you are not the one who will implement it: a plan
reviewed by the person invested in building it is not reviewed.

## Exploration -- what you read and do

- **Read the plan and the requirements** it claims to satisfy. Is the problem
  stated clearly -- what is wrong, for whom, and observed how?
- **Confirm the root cause.** Locate the code the plan touches and reproduce or
  trace the failure end to end. Do not accept the plan's assertion: a confirmed
  cause is evidence, a guessed one is a coin flip.
- **Search before judging duplication.** Grep the codebase, the standard library,
  and installed dependencies for what the plan proposes to build.
- **Map the impact radius.** Which modules does the plan touch, and for each, is
  touching it necessary?
- **Check the plan against the binding rules** -- module boundaries, ownership of
  facts, stated interfaces.
- **Judge the conditionals.** For each conditional criterion below, state
  whether it applies rather than skipping it silently.

## Criteria

**Required (always apply)**

1. **Problem statement** -- is the problem stated clearly: what is wrong, for
   whom, and how it is observed?
2. **Root cause confirmed, not guessed** -- is the cause evidenced (reproduced,
   traced end to end), or assumed?
3. **Modularity requirements respected** -- does the plan honor the project's
   module boundaries, ownership of facts, and stated interfaces?
4. **Impact radius minimized** -- is the change as small and as local as it can
   be while still correct? Which modules does it touch, and must it?
5. **No unnecessary duplication** -- does it re-implement something the codebase
   already has?

**Always-on additions**

6. **Verification plan** -- does the plan say how correctness will be shown, and
   at which level (module test vs system test)? A plan with no runnable check is
   unfinished.
7. **Interfaces and contracts stated** -- are the public surfaces, value shapes,
   and boundaries defined before implementation starts?
8. **Requirements allocated, assumptions surfaced** -- is each requirement owned
   by a module, and are the plan's assumptions named rather than hidden?
9. **No unrequested abstraction, config, or dependency** -- does it add
   structure "for later", or a new dependency for a few lines? Distinct from
   (5): this is *new* machinery that need not exist.

**Conditional (apply when the plan touches that area)**

10. **State and ownership impact** -- does it introduce new mutable state, and is
    its owning module named? Does it cross a thread boundary, and if so does it
    obey the concurrency rules?
11. **Safety at boundaries** -- does it keep input validation, error handling
    that prevents data loss, security, and accessibility intact? -- conditional,
    but never traded away.
12. **Risk and reversibility** -- are unknowns and assumptions called out, and
    can the change be staged or reverted if it is wrong?

## Findings

Return findings per the shared protocol (`review-independence`): a list of
findings, grounded in the plan and the contract. Report **rule violations by
rule-ID**; report everything else by its anchor -- a requirement, a `file:line`.
Not a form to fill in.
