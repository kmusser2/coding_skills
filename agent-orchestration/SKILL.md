---
name: agent-orchestration
description: >
  The parent agent's orchestration of independent review: when to invoke a
  reviewer subagent, the flow through both review gates, and the loops when a
  review finds defects. Language-agnostic.
license: MIT
compatibility: Language-agnostic
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Agent orchestration -- invoking reviewers

**Version:** 0.1 (draft).
**Status:** Normative. Maintained at the level of the harness and binding on
the project it is configured for, unless the user explicitly excludes this
skill, or a named statement in it, in that project's AGENTS.md. Silence is
not an exclusion.
**Scope:** the orchestrator's role -- **why** and **when** to invoke a reviewer
subagent, the flow through both gates, and the loops when a review finds defects.
**Role:** the orchestrator is the **parent agent** -- the one with the
interactive user session.

## Preconditions

This skill invokes **reviewer subagents**, so they must be configured:

- **Required:** the subagent types **`plan-reviewer`** (Gate 1) and
  **`code-reviewer`** (Gate 2). If either is missing, **warn the user that the
  orchestration skill cannot be applied** -- and do not fall back to reviewing
  your own work.
- **Required -- binding rules:** each reviewer must also carry the project's
  **binding-rule capability**. A reviewer without the rules cannot apply its
  criteria: if the rules are absent, **warn the user** and do not run the gate.
- **Optional:** **`explore`**, for retrieval that spares your context
  (*When to invoke a reviewer*). Its absence does not block orchestration.

The two reviewer types are configured with the matching capability --
`review-plan.json` for `plan-reviewer`, `review-code.json` for `code-reviewer` --
**plus** the project's binding-rule capability.

## The orchestrator is the parent agent

In this workflow, orchestration is a **judgment** made by the parent agent -- the
agent the user is talking to. It is not the harness.

- The parent agent decides when a change is non-trivial enough to review, what to
  freeze as the contract, and when the work is done.
- It delegates each review gate to a **separate reviewer subagent**, and never
  reviews its own work.
- It owns the plan, the decisions, and the integration.

## Why independent review

A reviewer that did not produce the artifact, and shares none of the producer's
reasoning, has a different failure surface -- it sees what the producer
rationalized away. That is the reason to seek an independent review, and the
reason the reviewer must be a *separate* agent rather than you re-reading the work
yourself: independence comes from separation, and a subagent is the clean way to
get it.

## When to invoke a reviewer

Independent review is for **non-trivial** changes; whether a change is
non-trivial is your judgment. Invoke a gate as its own step, by spawning a
**fresh reviewer subagent** -- *fresh* meaning newly created and independent of
anything that produced the work, not a hand-me-down context. Never review your
own work.

*Fresh* is not *disposable*: once spawned, a reviewer stays with the task, and
you consult that **same** reviewer again when you rework (*The loops*).

Review is not retrieval. To *gather information* -- investigate a question and
get a curated summary back -- use an **explore** subagent, which optimizes for a
compact answer that spares your context. Review is a reasoning-intensive role
that optimizes for *judgment*: reach for a reviewer when you need a verdict on an
artifact, not a summary of it. Spawn it fresh and **read-only -- PLAN-RO mode**:
a reviewer judges the workspace, it never changes it, so it gets no write
access to it.

There are two gates -- Gate 1 reviews the plan, before code; Gate 2 reviews the
result, after code:

| | **Gate 1 -- plan review** | **Gate 2 -- result review** |
|---|---|---|
| Object reviewed | the plan / requirements | the implemented artifact |
| Frozen contract | requirements + binding rules | the frozen plan + binding rules |
| Catches | wrong problem, guessed cause, missing requirements, scope creep, unowned facts, unstated interfaces, duplication | plan-to-code divergence, spec-vs-code disagreement, tests that do not test, boundary/safety gaps, a plan wrong in a way only the code reveals |

Give each reviewer the gate skill it needs -- `review-plan` for Gate 1,
`review-code` for Gate 2. The *binding rules* are the project's configured rule
capability -- the rule skills it carries. Name that capability when you freeze
the contract, so "fixed before review" has a referent.

## The flow

```
requirements -> create-plan -> review-plan -> code -> review-code -> done
                    ^              |              ^           |
                    +--- defects --+              +- defects -+
                       amend plan              fix code / amend plan
```

A defect found at the result review routes to whoever is wrong: to `code` if the
code is wrong, or back to `create-plan` if the *plan* is.

Each step in turn:

- **requirements** -- the user's request, clarified with the user.
- **create-plan** -- write the plan to its working file (*The plan*) for Gate 1
  to review.
- **review-plan** -- Gate 1 (`review-plan`), given the plan's path, run by a
  **`plan-reviewer`** subagent.
- **code** -- implement the frozen plan.
- **review-code** -- Gate 2 (`review-code`), given the frozen plan's path, run by
  a **`code-reviewer`** subagent.
- **done** -- the user gives final approval; the orchestrator ships the work,
  closes the reviewers, and deletes the plan file.

## The plan

Write the plan to a **gitignored path** in the workspace -- a Markdown working
file, not a repository asset. A plan is what you intend to do to the workspace,
not a deliverable of it, so it is never committed; it is a working artifact the
reviewers read by reference. (A typical home is a gitignored `.plans/` directory;
the project supplies the exact path.)

**What the plan contains.** At minimum:

- **Problem** -- what is wrong, for whom, observed how; and the *confirmed* root
  cause.
- **Requirements** -- what the change must satisfy. Where a requirements doc owns
  them, reference it and do not restate it; where none exists, this section **is**
  the requirement record, and it is frozen with the plan.
- **Allocation** -- each requirement to the module that owns it, and each test to
  the test module that runs it.
- **Tests** -- the module-level checks, and the system-level test(s) that only full
  integration can show.
- **Approach and risks** -- the change, its impact radius, the interfaces it
  touches, and the assumptions and unknowns.

A reviewer assesses this plan against the gate's criteria (`review-plan`).

- **Write it; do not paste it.** Hand a reviewer a **reference** -- the file's
  path -- not the plan text.
- **Update in place.** When the plan changes, edit the file and tell the reviewer
  what changed; it re-reads the file. The plan is never re-sent whole.
- **Freeze a revision per review.** A review judges one revision of the
  contract: record the plan's revision (a hash or version note), the
  binding-rule capability and its revision, and the revision of any referenced
  requirements doc -- so the contract under review is well defined.
- **Delete it when done.** Once the user approves the task and the work is
  committed, remove the plan file -- it was process state, not an asset.

## The loops

A review that finds defects does not end the flow; it routes back:

- **review-plan defects** -- amend the plan (*create-plan*), then review again.
- **review-code defects** -- fix the code (*code*), or, if the *plan* is what is
  wrong, amend the plan (*create-plan*, and re-run the plan review), then review
  again.

Run each loop with the **same** reviewer: **keep the subagent alive until the task
is done.** It has already learned the artifact, the contract, and the project, so
a deficiency you resolve and hand back is cheap for it to re-check -- where a
newly spawned reviewer would have to re-learn everything.

Because you are interactive with the user, **"done" is the user's call.** Gate
acceptance only moves the flow forward; the task ends when the user gives final
approval. Keep the reviewers alive across the loops, and even after a gate
accepts, until then -- and close them only after that approval. The contract is
fixed *for a given review*; amending the plan makes a new revision and re-freezes
it, and the reviewer re-checks against that revision.

## What the orchestrator must not do

- **Review its own work.** It delegates every gate; an agent cannot independently
  judge what it produced.
- **Edit a reviewer's findings.** It decides on the findings; it does not rewrite
  them.
- **Let the contract move under review.** Freeze it first.
- **Give a reviewer write access.** Reviewers run in **PLAN-RO** (read-only).
