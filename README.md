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

Configure an agent with a manifest and it takes on that bundle of guidance.
An agent may carry more than one: the review manifests, for instance, are
paired with a rule manifest, so a reviewer holds both its gate criteria and
the rules to judge against. The same skill may appear in several manifests, so
a project can pick the narrowest bundle that fits.

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
and errors, testing, service/protocol interfaces, concurrency design -- and
the lazy-solution discipline (`ponytail`), but none of the Python-specific
typing or naming rules. Also a sensible baseline while a project's language
is still undecided.

### `ponytail.json` -- making software as simple and maintainable as possible

**When would you use this:** When you want simplicity discipline on its own
terms -- any language, any size -- just the lazy-senior-dev principles (force
the laziest solution that actually works) without the fuller modularity and
concurrency rule sets. The minimal manifest.

### `agent-orchestration.json` -- the parent agent's review orchestration

**When would you use this:** Give this to the **parent agent** -- the one
holding the interactive user session. It is the orchestrator: it owns the flow
(`requirements -> create-plan -> review-plan -> code -> review-code -> done`) and
the loops when a review finds defects, delegates each gate to a separate reviewer
subagent, and decides when the work is done. It carries the orchestration
skill (`agent-orchestration`).

**Requires:** two reviewer subagent types -- **`code-reviewer`**, configured with
the `review-code.json` capability, and **`plan-reviewer`**, configured with
`review-plan.json`. If either is missing, the orchestration skill cannot be
applied. **`explore`** is optional (used for retrieval, to spare context).

**Note -- judgment, not hard gates.** Orchestration here is the *parent agent's
judgment*: the agent decides when a change is non-trivial, what to freeze as the
contract, and when the work is done. A more rigorous workflow could move those
decisions into the harness itself -- deterministic gating, enforced loops, a
machine-checkable contract. Apply this capability where that judgment-based model
fits the project; expect an agent (and the user) in the loop rather than hard
gates.

### `review-plan.json` -- independent review of a plan, by a subagent

**When would you use this:** Before implementing a change, when you want a
fresh subagent -- one that did not write the plan -- to judge it against the
requirements and the project's binding rules: is the problem clear, is the root
cause confirmed, does it respect modularity, is the impact radius minimal, is
existing functionality duplicated. It bundles the shared reviewer protocol
(`review-independence`) and the Gate 1 plan-review skill (`review-plan`). Pair
it with one of the rule manifests above so the reviewer knows the binding
rules.

### `review-code.json` -- independent review of a result, by a subagent

**When would you use this:** After implementing a change, when you want a fresh
subagent to judge the result against the frozen plan and the binding rules --
plan-to-code fidelity, whether the cause is really fixed, and whether the tests
actually test. It bundles the shared reviewer protocol (`review-independence`)
and the Gate 2 result-review skill (`review-code`). Pair it with one of the
rule manifests above.

## Maturity

A capability is **normative in force** the moment it is configured on a project:
agents treat it as binding. *Maturity* is a separate question -- how far the
capability has been settled and exercised -- and is tracked here, not in the
skills themselves (which all read as normative). Maturity is assessed per
**capability**, never per skill: a skill is only meaningfully evaluated in the
context of the capability it belongs to.

| Capability | Maturity | Notes |
|---|---|---|
| `ponytail.json` | stable | well-established heritage; the minimal manifest |
| `python.json` | active | full Python stack; under active development |
| `modularity.json` | active | language-neutral design rules; under active development |
| `agent-orchestration.json` | draft | new; not yet exercised end to end |
| `review-plan.json` | draft | new; not yet exercised end to end |
| `review-code.json` | draft | new; not yet exercised end to end |

**stable** -- settled and in use; changes are rare. **active** -- in active
development; its content is still being shaped. **draft** -- new; normative in
force, but not yet validated in practice.
