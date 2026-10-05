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
- State that changes after start-up belongs to an object, not to a module.
- **Carveout -- registration.** A registry may be *built* at import time and is
  read-only thereafter: a name populated by registration during import is a
  constant once import completes.
- Prefer a tuple, a `frozenset`, or a read-only mapping over a list, a set, or a
  dict at module scope.
- Expect these consequences if you break it: tests become order-dependent, the
  module stops being importable in isolation, and every reader must know the
  whole program's history to reason about one function.
- *Test:* can anything rebind this name, or mutate its value, at run time? If
  yes, it is not a constant.

**B2. Importing a module does no work.** Import must not perform I/O,
open a network connection, spawn a process, read or write a file, register a
global handler, or monkeypatch another module.
- Work belongs in a function the caller invokes, or in an explicit startup call.
  A module that does work at import time cannot be tested in isolation.
- **Carveout -- declarative registration.** A module may register its names at
  import time into a registry designed for it: a route table, a plugin hook
  set, a class registry. The registration records metadata and nothing else --
  no I/O, no computation a caller would need to control -- and the effect is
  deterministic and enumerable: importing the module and reading the registry
  shows all of it.
- What stays banned: OS or runtime-global handlers (`signal.signal`,
  `logging.basicConfig`), monkeypatching another module, and anything a caller
  would need to time, retry, or recover from.
- *Test:* does `import x` **do work**, or change anything outside `x` that is
  not a registry designed for registration? If so, that work belongs behind a
  call.

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

**B4. Every object has one owner; mutation is the owner's to initiate.** An object
is owned by exactly one module, and only that module may change it on its own
initiative.
- The owner may **request** another module to change its object -- sorting an
  array, filling a buffer. The request is the call: the mutation happens during
  it, at the owner's initiative, and ends with it. Python states this in the
  parameter's type -- a mutable type (`MutableSequence`, `list`, `bytearray`)
  where the callee will change the value, a read-only type (`Sequence`,
  `Mapping`) where it will not. This is the C++ non-const reference contract;
  checkers enforce the read-only side, and the mutable side is the statement. A
  name that marks the mutation (`sort_in_place`) is welcome where the type
  cannot say it.
- Across a thread boundary nothing mutable is shared: a value is immutable, or
  handed over outright with the giver keeping no reference (C1).
- A mutable global is not allowed. That claim is B1's, and this rule points at
  it.
- An object changing itself through its own methods is not mutation from
  outside, and is not this rule's business.
- *Test:* who can change this object on its own initiative? Name one module. And
  does a callee's signature say when it will change a value it is given?

**B5. Public boundaries are narrow, and no public behaviour is chosen by a
mode flag.** A public function takes what it needs -- the values that
parameterize one computation -- not a context bag or a god object. A parameter
of a public function that selects between two behaviours is two public
functions: split it. A parameter that tunes one behaviour -- a limit, a
tolerance, a direction -- is part of one computation and stays.
- A **mode** flag changes which work is done, or what kind of result comes
  back. Describing the function then needs the word "or": it renders text *or*
  HTML.
- An **option** flag adjusts the same work: `sorted(xs, reverse=True)` is one
  sort, run the other way round. Splitting it multiplies names without removing
  a mode.
- **The split public functions wrap one private implementation.** When most of
  two behaviours is common, the public functions state the choice and both call
  a private helper that carries the mode. The mode lives where the commonality
  is exploited -- never at a public boundary. A private helper is exempt from
  this rule: it sits behind the split public names, and its callers are close.
- When the same group of options travels together across many call sites,
  gather it in a small value built for that purpose -- not in a general context
  object.
- *Test:* state what this public function does in one clause. Does the
  statement need "or", or name a mode?

## C. Concurrency

The cross-thread rules live in the companion skill `threading` and are not
restated here -- a restatement would be a second owner (A1). Pointers: C1
(state ownership), C2 (workers), C3 (cancellation), C4 (locks), C5
(latency-sensitive loops). B4 above governs every value that crosses a thread
boundary.

## D. Values and errors

**D1. Named sets are enumerations; absence is a sentinel.** A value drawn from a
fixed, small set is an enumeration -- never a bare string, a bare integer, or
`None` standing as a member of the set.
- A bare value fails silently when misspelled -- `"unkown"` travels as a valid
  state forever. An enumeration fails loudly and is discoverable.
- When the value is serialized, prefer an enumeration whose values are the
  stored or wire strings, so the representation stays explicit.
- `None` is a legitimate "no value" only where it is not a legal domain value.
  When a parameter must distinguish *not passed* from every value that can be
  passed -- `None` included -- the default is a sentinel object of its own,
  compared by identity (`dataclasses.MISSING` is the model). The sentinel
  belongs to no set: it marks absence.
- Many sentinel-default parameters in one signature is itself a smell -- a
  function taking many optional values is often several functions (B5).
- *Test:* is this value one of a known set? If so, name the set. Does this
  marker assert that nothing was passed? If so, is it an object no value can
  equal?

**D2. Errors are explicit.** No bare `except:`, and no handler that swallows an
exception without acting on it or reporting it.
- Convert an error at the boundary where you can add meaning; let it propagate
  where you cannot.
- The exceptions a function raises are part of its contract. Document them.
- *Test:* if this fails, does anyone find out?

**D3. The public surface is stated, not inferred.** A module's API is the set of
names it declares as public -- documented, and where the language supports it,
declared explicitly (for example, `__all__`) and typed (F1).
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

## F. Types

**F1. The public surface is annotated; the private surface may be.** Every public
function and method states the types of its parameters and of its return. A
private function's annotations are its author's choice -- but if present, they
obey the rules below like any other.
- The annotation is part of the contract the public surface states (D3): it is
  what a caller can rely on, and what a checker can verify. An unannotated
  public parameter is an unstated contract.
- An annotation that is present is a claim, and may not be looser than the code:
  no `Any` to silence a checker, no bare container to dodge a shape.
- *Test:* can a caller know, without reading the body, what this function takes
  and returns?

**F2. `Any` is prohibited; `object` is honest.** `Any` asserts "trust me": every
operation on it succeeds, and the blindness spreads to everything derived from
it. An `Any` annotation is, to a checker, no annotation at all -- and an `Any`
return gives every caller nothing.
- Where the type is genuinely unknown, annotate `object`: it says "I do not
  know", takes anything on input, and forces a narrowing before use. Mistakes
  fail loudly instead of silently.
- **Carveout -- the dynamic seam.** `Any` is allowed where genuinely dynamic
  things meet typed code: dynamic dispatch, a foreign interface, untyped data.
  It lives in the boundary adapter alone; everything that leaves the boundary
  is typed.
- **Carveout -- dynamic plumbing.** Machinery that exists to forward values
  unseen (`**kwargs` of a decorator factory, a proxy) may take `Any` where
  `object` would defeat its purpose. That is the project's judgment call, not a
  licence elsewhere.
- *Test:* if this annotation were deleted, would checking change at all? If not,
  it is decoration.

**F3. A container names what it holds.** A bare `dict`, `list`, `set`, `tuple`,
`Callable`, or `Iterable` is `dict[Any, Any]` in different clothes (F2).
Parameterize every generic: `dict[str, User]`, `tuple[str, int]`,
`Callable[[int], str]`.
- If what the container holds cannot be named, the shape is not yet understood
  -- or it is several shapes, and wants named fields (F4).
- *Test:* does this annotation say what is inside?

**F4. Values that travel have named fields.** A value passed or returned across
a function or module boundary carries its meaning in field names -- a small
class (a frozen data class, a named tuple), never a bare tuple, never a
`dict[str, Any]`, never a positional pair whose order every caller must remember.
- Named fields make the call site read (`order.total` instead of `order[3]`),
  make renames findable, and give the value's documentation one home (A2).
- A **frozen data class** is several named facts travelling together. An
  **enumeration** is one value drawn from a named set (D1). The shape follows
  the claim: one-of-a-set is an enum, several-named-values is a class. An enum
  whose members each carry data is usually a class; a class whose fields are all
  selectors is usually an enum (see Examples).
- Local values that do not leave the function are exempt: a pair unpacked on
  the next line is fine.
- A `dict` as the wire or stored form is exempt at the boundary that serializes
  -- convert there.
- *Test:* at a call site, does this value's use read as a name or as an index?

## Examples

Each example is self-contained; none refers to a particular project or file.

**Pointer versus narration (A2).**
- Fine: "Callers must call `open()` before `write()`." A requirement on this
  symbol's own interface; it stays true as callers are added, renamed, removed.
- Defect: "The only caller is `run_turn()`." It names a consumer, so renaming
  that caller makes the sentence wrong.

**One fact, one owner (A1).**
- A rule about how a list is split on a separator is stated in a
  specification, restated in a short summary, implemented in a production file,
  and implemented again in a prototype copy of that file. Changing the rule
  means editing four places: one owner and three copies. Point the three at the
  owner, or generate them from it.
- A help listing of identifiers must track the specification by hand. Either
  generate it from the specification, or pin it with a test that fails when the
  two diverge. Then it is derived, not a second author.

**Identical text, different claims (A1).**
- One function's own docstring uses `pattern="int|float"` to demonstrate that
  function's parameters; a syntax specification uses the same string to define
  what a pattern means. The text matches; the claims do not. Do not
  "de-duplicate" them -- removing either loses a different fact.

**A flag argument, split (B5).**
- `render(text, as_html=True)` is two public functions: `render_text(text)` and
  `render_html(text)`. Every caller states which it wants, and neither public
  function carries a mode.
- Both call `_render(text, as_html)`: one private implementation exploiting the
  shared 90%. The flag exists where the code is common, not where the contract
  is stated.
- `sorted(xs, reverse=True)` is one function: the flag tunes the same
  computation rather than selecting another one.

**An enum or a frozen data class (F4).**
- `Status` is one of `queued`, `running`, `done` -- one value from a named set:
  `Status` is an enumeration.
- `Job(id=7, owner="ada", status=Status.queued)` is several named facts
  travelling together: `Job` is a frozen data class, and its `status` field is
  the enum.
- `{"id": 7, "status": "queued"}` is the same claim with no owner -- a bare dict
  (F3) around a bare string (D1). When the facts are one-of-a-set, the shape is
  an enum; when they are several named values, it is a class.

## What this document is not

- It is not a formatting or naming-style guide.
- It describes no tooling and ships no checker.
- It authorizes no refactor, and no cleanup of code that predates it.
- It is not any project's policy, and it does not override a project's own
  conventions.
