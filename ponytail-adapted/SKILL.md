---
name: ponytail-adapted
description: >
  Adapted from the ponytail project (MIT, (c) 2026 DietrichGebert) -- the lazy
  senior dev principles: forces the laziest solution that actually works.
license: MIT
compatibility: Language-agnostic
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Ponytail (adapted) -- the lazy senior dev principles

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

## Sources

Adapted from Ponytail, https://github.com/DietrichGebert/ponytail, MIT License,
(c) 2026 DietrichGebert. This document paraphrases the project's principles into
this family's format; upstream owns its claims (A1), and quoted phrases are
marked. The full license text is in the upstream LICENSE file. Snapshot:
fetched 2026-06-05.

Upstream also ships companion workflows (`ponytail-audit`, `ponytail-debt`,
`ponytail-gain`, `ponytail-help`, `ponytail-review`); they are workflow
procedures, not principles, and are not restated here -- see upstream if you
want them.

**Scope.** How much code to build: the laziest solution that actually works.
P1 climbs a ladder of lazier options before writing code; P2 fixes causes, not
symptoms; P3 deletes before it adds; P4 refuses to be lazy about understanding
or about safety; P5 marks deliberate simplifications; P6 leaves one runnable
check behind.

**Family.** Rule ids are P1--P6 (P for ponytail), family-wide and stable.
**ponytail governs how much code you build; the family governs how what you
build is structured.** In particular, H1's requirements docs and test entry
points are documents, and ponytail's "fewest files" does not reach them. Naming
(N1--N4), modularity (A/B/C/D/E/G/H), typing (`modular-python`) and concurrency
(`threading`) are unchanged by this skill and are not restated here (A1).

**Force.** A statement marked **[M]** is mandatory; one marked **[G]** is
guidance -- the family's default judgment, replaceable by the project's own
judgment without ceremony. A rule's headline and its opening statement carry
the headline's tag; each bullet carries its own tag when it adds a norm.
Unmarked text -- rationale, examples, and the *Test* questions -- binds
nothing. A mandatory statement may not be overridden unilaterally by the
agent applying it: only an explicit statement in the project owner's rules
may except it (`modularity`, *Exceptions*). The decisions the ladder asks for
are judgment; the discipline of climbing it is mandatory.

**Intensity.** A parameter, not a rule. *lite:* build what was asked, name the
lazier alternative in one line. *full* (default): the ladder is enforced. *ultra:*
YAGNI extremist -- deletion before addition, and the requirement itself gets
challenged.

## P. The principles

**P1. [M] Climb the ladder; stop at the first rung that holds.** Before writing
code, understand the problem: read the task and the code it touches, and trace
the real flow end to end. Then climb, stopping at the first rung that solves it:
1. Does this need to exist at all? A speculative need is skipped, and the skip
   is stated in one line.
2. Does it already exist in this codebase? Look before you write.
3. Does the standard library do it?
4. Does the native platform feature do it? (`<input type="date">` over a picker
   library; CSS over JavaScript; a DB constraint over application code.)
5. Does an already-installed dependency do it? Never add a new dependency for a
   few lines.
6. Can it be one line?
7. Only now: the minimum code that works.
- **[M]** Two rungs would hold? Take the higher one.
- *Test:* which rung stopped you -- and did you climb only after tracing the
  real flow?

**P2. [M] Fix the root cause, not the symptom.** A report names a symptom. Grep
every caller of the function you are about to touch, and fix the shared
function once: one guard in the shared function beats one per caller, and
patching only the named path leaves the siblings broken.
- *Test:* when this bug recurs from the sibling path, is the fix already there?

**P3. [M] Deletion over addition.** No unrequested abstractions: no interface with
one implementation, no factory for one product, no configuration for a constant.
No boilerplate or scaffolding "for later". **[G]** Boring over clever. Fewest files
possible (subject to the Family note re H1). The shortest working diff wins --
but only after understanding: the smallest change in the wrong place is a
second bug. A complex request gets the lazy version shipped *and* questioned in
the same response ("Did X; Y covers it. Need full X? Say so") -- never stall on
an answer you can default. Two standard-library options of the same size? Take
the edge-case-correct one: lazy means less code, not a flimsier algorithm.
- *Test:* what did you not build, and what is the trigger to build it?

**P4. [M] Never lazy about understanding; never lazy about safety.** Never simplify
away input validation at trust boundaries, error handling that prevents data
loss, security, accessibility, or anything explicitly requested -- if the user
insists, build it; do not re-argue. Never lazy about comprehension either:
trace every file the change touches first. And the physical world is not lazy
-- real clocks drift, sensors read off -- so leave the calibration knob.
- *Test:* what does this simplification stop being true at?

**P5. [M] Deliberate simplifications are marked.** A `ponytail:` comment names both
the ceiling and the upgrade path:
- `# ponytail: global lock, per-account locks if throughput matters`
- *Test:* does the comment name both the ceiling and the upgrade path?

**P6. [M] Non-trivial logic leaves one runnable check.** Any branch, loop, parser,
or money/security path leaves behind ONE smallest failing-if-broken check: an
assert-based `demo()`/`__main__` self-check, or one `test_*.py`. No frameworks,
no fixtures, no per-function suites unless asked. Trivial one-liners need no
test -- YAGNI applies to tests too.
- *Test:* what fails if this logic breaks?

## Examples

**The cache (P1, paraphrased from upstream).** "Add a cache" -- the ladder
stops at rung 6: `functools.lru_cache` is a one-liner on the hot function. The
custom cache class on rung 7 is not built; the trigger to build it is
`lru_cache` measurably falling short (eviction policy, per-tenant limits).
Marked where the ceiling matters: `# ponytail: lru_cache unbounded per key
shape, custom cache if memory becomes the constraint`.

## What this document is not

- It is not a copy of upstream. Where an upstream claim appears here, upstream
  owns it (A1); this document paraphrases into the family's format.
- It governs what you build, not how you talk -- output brevity and mode
  behavior are out of scope (upstream says this too).
- It restates no principle that `modularity` or its siblings own (A1): P6 asks
  for one minimal check per change; the E-rules govern test layout. P1--P6 say
  how much code; A/B/C/D/E/G/H say how the code you do build is shaped.
- It is not any project's policy, and it does not override a project's own
  conventions.
