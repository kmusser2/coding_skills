---
name: review-code
description: >
  Reviewing a result: judging implemented code against the frozen plan and the
  requirements -- does the code do what the plan said, does it meet the
  requirements, is the cause actually fixed, do the tests really test, and is the
  public surface as stated? Language-agnostic.
license: MIT
compatibility: Language-agnostic
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Reviewing a result

**Version:** 0.1 (draft).
**Status:** Normative. Maintained at the level of the harness and binding on
the project it is configured for, unless the user explicitly excludes this
skill, or a named statement in it, in that project's AGENTS.md. Silence is
not an exclusion.
**Scope:** the reviewer's job when reviewing a result -- focus, exploration, and
criteria.
**Contract:** the frozen plan, plus the project's binding rules.
**Protocol:** you honor `review-independence`, which owns independence, the frozen
contract, the partner objective, the findings, and who decides. This skill owns
only your focus, exploration, and criteria.

## Focus

Reviewing a result asks whether the work that was done is correct and complete --
whether the code does what the plan said, whether the plan turned out to be
right, and whether the evidence (the tests) actually supports the claim. It
catches what a plan review structurally cannot: a plan wrong in a way only the
code reveals, and silent drift between plan and code.

## Exploration -- what you read and do

- **Read the diff and the frozen plan side by side.** For each plan claim,
  verify the code does it; record every deviation.
- **Run the runnable check** the plan promised. Confirm it actually asserts --
  that it would fail if the logic broke -- rather than passing vacuously.
- **Read the tests.** Do they test the unit directly, scoped to it, and cover the
  branches the change introduces?
- **Surface spec-vs-code disagreements.** Where specification and code disagree,
  state which you believe owns the claim -- is the code the bug, or the spec? --
  as a finding to be resolved.
- **Check the boundaries.** Input validation, error handling that prevents data
  loss, security, accessibility.
- **Look for leftovers.** Dead code, scaffolding, commented-out blocks,
  unrequested abstraction.
- **Judge the conditionals.** For each conditional criterion below, state
  whether it applies rather than skipping it silently.

## Divergence is a finding

When the implementation departs from the plan, that is itself a finding: the
plan is wrong or the code is -- which the orchestrator resolves. Surface it; do
not silently accept it. Silent drift is how the review becomes theater.

## Criteria

**Required (always apply)**

1. **Plan-to-code fidelity** -- does the code do what the frozen plan said? Is
   every deviation surfaced and justified, or flagged?
2. **Requirements met** -- does the result satisfy what the change was for, not
   merely what the plan said?
3. **Root cause actually fixed** -- is the cause fixed, or is the symptom
   masked?
4. **Modularity respected in the code** -- do the real module boundaries,
   ownership, and public surfaces hold -- declared and typed?
5. **Impact radius as promised** -- no wider than the plan, no collateral
   edits.
6. **No duplication introduced** -- nothing re-implemented that already exists.
7. **Verification present and real** -- a runnable check exists and would fail
   if the logic broke.
8. **Interfaces as stated** -- the implementation matches the contracts the plan
   stated, or the plan has been amended to match.
9. **No unrequested abstraction, config, or dependency** -- none added that need
   not exist.
10. **Leftovers removed** -- dead code and scaffolding gone.

**Conditional (apply when the change touches that area)**

11. **Safety at boundaries preserved** -- validation, error handling that
    prevents data loss, security, accessibility.
12. **Concurrency rules honored** -- if the change crosses threads or introduces
    shared state.
13. **Naming conforms** -- names carry their constancy and visibility, when the
    change introduces names worth checking.

## Findings

Return findings per the shared protocol (`review-independence`): a list of
findings, grounded in the result and the contract. Report **rule violations by
rule-ID**; report everything else by its anchor -- a requirement, a `file:line`.
Not a form to fill in.
