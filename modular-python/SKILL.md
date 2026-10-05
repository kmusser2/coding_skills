---
name: modular-python
description: >
  Architectural principles for designing maintainable Python code bases
  which are robust to future requirements changes.
license: Apache-2.0
compatibility: Requires Python 3.11+
metadata:
  author: kmusser@idi-software.com
  version: "1.0"
---

# Python Modular Design -- portable guidance

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

## How to apply this

- **Precedence.** A project's own stated convention wins. Where the project is
  silent, these rules are the default.
- **Scope of application.** These rules govern the code you are writing or
  editing. In a codebase that predates them they forbid *new* violations and
  authorize no repairs: never fix an existing violation as a side effect of
  unrelated work, and never read this document as a mandate to refactor.
- **Enforcement belongs to the project.** This document ships no checker and no
  exception list. A project that wants these rules enforced owns that mechanism,
  and owns its exceptions.
- **Principles travel; parameters do not.** Each rule below states a general
  claim. Its concrete expression -- naming style, thresholds, tooling -- is the
  project's to choose.
- **Defer to the project's own rule owners.** Before changing behaviour a
  project documents, find that document and follow it. This document cannot
  index a project it has not seen.

Each rule ends with a test -- the question to ask of the code in front of you.

## A. Ownership of facts and prose

**A1. One fact, one owner.** Ownership is per *claim*, not per file and not per
subject. A claim is one thing that must stay true: a rule, a contract, an
invariant, a canonical example, an algorithm, a default.
- Exactly one owner: a section of a design document, **or** one symbol in one
  source file. Never two.
- A specification and its implementation own *different* claims about the same
  subject. The spec owns **what/why** -- required behaviour, names, ranges,
  limits, the canonical example; the source owns **how** -- signature, mechanism,
  the error text it raises. Neither restates the other's claim. That is what
  makes a design document and its source a valid pair rather than a duplicate.
- **Ownership test:** if the two disagree, which one is a bug? That one owns the
  claim; the other must **point**, using a stable name (a symbol, a rule id, a
  section heading) -- never a restatement.
- **Identical text is not the same claim.** Two places may carry the same string
  while asserting different things. De-duplicate claims, not text.
- A **hand-maintained** copy is a defect. A generated copy, or one pinned by a
  test that fails on divergence, is not: it can no longer drift.
- An **algorithm** has one home. A prototype that reproduces production code, or
  a second copy of a parser, a validator, a schema, is a second owner, and every
  change to the fact becomes a two-file change.
- *Test:* if changing X requires editing a place that is not X, that place is a
  copy -- make it a pointer, or make it derived.

**A2. Documentation belongs to the module it documents.** A docstring, comment,
or document section is owned by the symbol or module it documents, and states
*that* symbol's claim: what it guarantees, what it requires of its caller, what
it raises.
- Never name or narrate another module's members, call sites, consumers, or
  internals.
- A cross-module reference must be a **pointer to a public name** -- never a
  description of its behaviour, and never a location (a line number, a commit, a
  file path).
- "The caller" as a **generic role** is fine: "callers must call `open()` before
  `write()`" is a claim about this symbol's own interface, and it survives every
  caller changing. Naming a **specific** caller is not.
- An aggregate document indexes and points; it does not restate what a module's
  own documentation already says.
- Exemption: a navigational index and an exception list may name other modules'
  members -- that is their whole function. They still may not restate behaviour.
- *Test:* if a change in another module makes this sentence wrong, the sentence
  is in the wrong place.

## B. State and boundaries

**B1. Module-level names are constants.** A module-level name is bound once and
never rebound, and its value is immutable.
- State that changes at run time belongs to an object, not to a module.
- Prefer a tuple, a `frozenset`, or a read-only mapping over a list, a set, or a
  dict at module scope.
- Expect these consequences if you break it: tests become order-dependent, the
  module stops being importable in isolation, and every reader must know the
  whole program's history to reason about one function.
- *Test:* can anything rebind this name, or mutate its value, at run time? If
  yes, it is not a constant.

**B2. Importing a module does nothing observable.** Import must not perform I/O,
open a network connection, spawn a process, read or write a file, register a
global handler, or mutate another module.
- Work belongs in a function the caller invokes, or in an explicit startup call.
  A module that does work at import time cannot be tested in isolation.
- *Test:* does `import x` change anything outside `x`? If so, that work belongs
  behind a call.

**B3. A module's private members are its own.** A name beginning with an
underscore belongs to the module that defines it; no other module reads or calls
it. This holds for instances as much as for modules.
- The language cannot enforce this. The convention **is** the rule, and the
  absence of enforcement is not permission. Type checkers do not treat a leading
  underscore as protected -- do not rely on one to notice.
- If an outside caller needs different behaviour, that is a signal to discuss a
  **public** interface change -- never a reason to reach across the boundary, and
  never a reason to add a public wrapper as a workaround.
- Inside one module, one object reaching into another object's private members is
  poor practice rather than a boundary violation: prefer not to, and give the
  other object a public method when the need is real.
- *Test:* does the name begin with an underscore, and live in a different module
  from the one using it?

**B4. What crosses a boundary is immutable, or ownership is transferred.** A
value handed to another module or another thread is either immutable, or handed
over outright with the giver keeping no reference to it.
- Prefer a frozen data class, a tuple, or a read-only mapping to a mutable object
  shared by reference.
- *Test:* after the handoff, can two parties mutate the same object?

**B5. Boundaries are narrow, and behaviour is not chosen by a flag.** A function
takes what it needs, not a context bag or a god object. A boolean parameter that
selects between two behaviours is two functions -- split it.
- *Test:* can you describe what this function does without describing a mode?

## C. Concurrency

**C1. State has exactly one owning thread.** Every piece of mutable state is
owned by one thread. A thread that does not own it may not read or write it
directly.
- Cross-thread communication happens only through the owning thread's channel: a
  queue it drains, or a message it reads -- never by calling into the owner's
  objects.
- The owner of the user interface is a single thread, and all view mutation
  happens there.
- *Test:* if two threads can reach this value, name the channel one of them goes
  through.

**C2. Threads are bounded, daemons, and end.** Create a thread for one long
operation the owning thread must not block on -- not one per item.
- A worker is a daemon with a defined end: it stops when its work ends, when it
  is cancelled, or when the process exits. Nothing waits forever.
- *Test:* how does this thread end, and what happens if it never does?

**C3. Cancellation is an event, not a flag someone else sets.** A thread that can
be cancelled observes a cancellation event, or an equivalent predicate, and
checks it at loop boundaries.
- Do not poll a shared mutable flag from outside, and do not stop a thread by
  mutating its state.
- Cancellation must be observable while a blocking wait is in progress: use a
  bounded timeout, or a wait that the cancellation interrupts.
- *Test:* can this thread be asked to stop while it is blocked?

**C4. A lock guards one object's state, briefly.** A lock is a private member of
the object whose state it guards, and it is held only around the mutation of that
state -- never across I/O, a callback, or a blocking queue put.
- *Test:* can this lock be held while the thread waits on something else?

**C5. The owning thread never blocks.** The thread that owns the user interface,
or any latency-sensitive loop, does no sleeping, no joining, no network I/O, and
no long computation. That is what the worker exists for.
- *Test:* what is the longest this loop can take before it can respond again?

## D. Values and errors

**D1. Enumerations, not sentinels.** A value drawn from a fixed, small set is an
enumeration -- not a bare string, a bare integer, or `None` used as a marker.
- Sentinels compare equal to nothing meaningful and fail silently when misspelled;
  an enumeration fails loudly and is discoverable.
- When the value is serialized, prefer an enumeration whose values are the stored
  or wire strings, so the representation stays explicit.
- *Test:* is this value one of a known set? If so, name the set.

**D2. Errors are explicit.** No bare `except:`, and no handler that swallows an
exception without acting on it or reporting it.
- Convert an error at the boundary where you can add meaning; let it propagate
  where you cannot.
- The exceptions a function raises are part of its contract. Document them.
- *Test:* if this fails, does anyone find out?

**D3. The public surface is stated, not inferred.** A module's API is the set of
names it declares as public -- documented, and where the language supports it,
declared explicitly (for example, `__all__`).
- A name is not public because it happens to lack a leading underscore; it is
  public because the module says so.
- *Test:* where does this module say what you are allowed to use?

## E. Tests

**E1. A module is testable without starting the application.** A module's
behaviour can be exercised by calling it directly -- no program launch, no
server, no user interface.
- A test that must start the application in order to reach a module is evidence
  that the module's dependencies are not injected. Fix the seam, not the test.
- *Test:* can this module be tested with the program not running?

**E2. Tests are scoped to the unit under test.** Keep module-scope tests (one
module, its collaborators replaced) separate from integration tests (several
modules, or the whole program, wired together).
- Mixing both in one place makes a single module change fan out into the
  integration suite, and a failure no longer tells you which layer is wrong.
- *Test:* when this test fails, does its name tell you whether the unit or the
  assembly broke?

## Examples

Each example is self-contained; none refers to a particular project or file.

**Pointer versus narration (A2).**
- Fine: "Callers must call `open()` before `write()`." A requirement on this
  symbol's own interface; it stays true as callers are added, renamed, removed.
- Defect: "The only caller is `run_turn()`." It names a consumer, so renaming
  that caller makes the sentence wrong.

**One fact, one owner (A1).**
- A rule about how a directive splits its list on a separator is stated in a
  specification, restated in a short summary page, implemented in a production
  file, and implemented again in a prototype copy of that file. Changing the rule
  means editing four places: one owner and three copies. Point the three at the
  owner, or generate them from it.
- A help message that lists rule ids must track the specification by hand. Either
  generate it from the specification, or pin it with a test that fails when the
  two diverge. Then it is derived, not a second author.

**Identical text, different claims (A1).**
- One function's own docstring uses `pattern="int|double"` to demonstrate that
  function's parameters; a syntax specification uses the same string to define
  what a separator does. The text matches; the claims do not. Do not
  "de-duplicate" them -- removing either loses a different fact.

**A flag argument, split (B5).**
- `render(text, as_html=True)` is two functions: `render_text(text)` and
  `render_html(text)`. Every caller now states which it wants, and neither
  function carries a mode.

## What this document is not

- It is not a formatting or naming-style guide.
- It describes no tooling and ships no checker.
- It authorizes no refactor, and no cleanup of code that predates it.
- It is not any project's policy, and it does not override a project's own
  conventions.
