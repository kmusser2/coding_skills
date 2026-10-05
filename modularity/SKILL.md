---
name: modularity
description: >
  Language-independent principles for modular design -- ownership of facts,
  module boundaries, values and errors, testing, service and protocol
  interfaces, requirements decomposition -- for code bases that are robust to
  future requirements changes. Any language.
license: MIT
compatibility: Any language
metadata:
  author: kmusser@idi-software.com
  copyright: (c) 2026 kmusser@idi-software.com
  acknowledgment: The author appreciates assistance from MiMo-V2.6-Pro and Deepseek-v4.1-Flash
  version: "0.1"
---

# Modular design -- portable guidance

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

**Scope.** Module decomposition in any language: ownership of facts and
documentation, state and boundaries, values and errors, testing, interfaces,
and the decomposition of requirements. The rules state design claims; the
language feature or library that expresses them is a parameter.

**Family.** Rule ids are family-wide and stable. The concurrency rules (C1--C5)
live in the companion skill `threading`; the Python typing rules (F1--F4) live
in the companion skill `modular-python`. This document indexes them and does
not restate them (A1).

## How to apply this

- **Precedence.** Where a project's own rules explicitly state an exception to
  a mandatory statement (see *Exceptions*), the exception wins within its
  stated scope. Where the project is silent, these rules are the default.
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
- **Force.** A statement marked **[M]** is mandatory; one marked **[G]** is
  guidance -- the family's default judgment, which a project may replace with
  its own judgment without ceremony. A rule's headline and its opening
  statement carry the headline's tag; each bullet carries its own tag when it
  adds a norm, and a differing force is tagged where it appears. Unmarked text
  -- rationale, examples, consequences, and the *Test* questions -- explains
  and binds nothing.
- **Exceptions.** A mandatory statement may not be overridden unilaterally by
  the agent applying it. It binds unless the project owner's own rules
  explicitly except it: the project document must name the rule id (or quote
  the statement) and state the exception's scope. Silence is not an exception,
  and neither is a general "our conventions differ". Code that predates the
  rule is governed by *Scope of application* -- no new violations, no mandated
  repairs. The family's own carveouts are part of the rule they appear in and
  need no exception. A checker enforces mandatory statements only; guidance is
  judgment.

Each rule ends with a test -- the question to ask of the code in front of you.

## A. Ownership of facts and prose

**A1. [M] One fact, one owner.** Ownership is per *claim*, not per file and not per
subject. A claim is one thing that must stay true: a rule, a contract, an
invariant, a canonical example, an algorithm, a default.
- **[M]** Exactly one owner: a section of a design document, **or** one symbol in one
  source file. Never two.
- **[M]** A specification and its implementation own *different* claims about the same
  subject. The spec owns **what/why** -- required behaviour, names, ranges,
  limits, the canonical example; the source owns **how** -- signature, mechanism,
  the error text it raises. Neither restates the other's claim. That is what
  makes a design document and its source a valid pair rather than a duplicate.
- **Ownership test:** if the two disagree, which one is a bug? That one owns the
  claim; the other must **point**, using a stable name (a symbol, a rule id, a
  section heading) -- never a restatement.
- **[M] Identical text is not the same claim.** Two places may carry the same string
  while asserting different things. De-duplicate claims, not text.
- **[M]** A **hand-maintained** copy is a defect. A generated copy, or one pinned by a
  test that fails on divergence, is not: it can no longer drift.
- **[M]** An **algorithm** has one home. A prototype that reproduces production code, or
  a second copy of a parser, a validator, a schema, is a second owner, and every
  change to the fact becomes a two-file change.
- *Test:* if changing X requires editing a place that is not X, that place is a
  copy -- make it a pointer, or make it derived.

**A2. [M] Documentation belongs to the module it documents.** A docstring, comment,
or document section is owned by the symbol or module it documents, and states
*that* symbol's claim: what it guarantees, what it requires of its caller, what
it raises.
- **[M]** Never name or narrate another module's members, call sites, consumers, or
  internals.
- **[M]** A cross-module reference must be a **pointer to a public name** -- never a
  description of its behaviour, and never a location (a line number, a commit, a
  file path).
- **[M]** "The caller" as a **generic role** is fine: "callers must call `open()` before
  `write()`" is a claim about this symbol's own interface, and it survives every
  caller changing. Naming a **specific** caller is not.
- **[M]** An aggregate document indexes and points; it does not restate what a module's
  own documentation already says.
- Exemption: a navigational index and an exception list may name other modules'
  members -- that is their whole function. They still may not restate behaviour.
- *Test:* if a change in another module makes this sentence wrong, the sentence
  is in the wrong place.

## B. State and boundaries

**B1. [M] Module-level names are constants.** A module-level name is bound once
and never rebound, and its value is immutable.
- **[M]** State that changes after start-up belongs to an object, not to a module.
- **Carveout -- registration.** A registry may be *built* at import time and
  is read-only thereafter: a name populated by registration during import is a
  constant once import completes.
- **[G]** Prefer an immutable collection -- in Python, a tuple, a `frozenset`, or a
  read-only mapping -- over a mutable one at module scope.
- Expect these consequences if you break it: tests become order-dependent, the
  module stops being importable in isolation, and every reader must know the
  whole program's history to reason about one function.
- *Test:* can anything rebind this name, or mutate its value, at run time? If
  yes, it is not a constant.

**B2. [M] Loading a module does no work.** Loading and initializing a module --
importing it, in Python -- must not perform I/O, open a network connection,
spawn a process, read or write a file, register a global handler, or
monkeypatch another module.
- **[M]** Work belongs in a function the caller invokes, or in an explicit startup
  call. A module that does work at import time cannot be tested in isolation.
- **Carveout -- declarative registration.** A module may register its names at
  import time into a registry designed for it: a route table, a plugin hook
  set, a class registry. The registration records metadata and nothing else --
  no I/O, no computation a caller would need to control -- and the effect is
  deterministic and enumerable: importing the module and reading the registry
  shows all of it.
- **[M]** What stays banned: OS or runtime-global handlers (`signal.signal`,
  `logging.basicConfig`), monkeypatching another module, and anything a caller
  would need to time, retry, or recover from.
- *Test:* does `import x` **do work**, or change anything outside `x` that is
  not a registry designed for registration? If so, that work belongs behind a
  call.

**B3. [M] A module's private members are its own.** A name the module marks
private -- an underscore prefix, in Python -- belongs to the module that
defines it; no other module reads or calls it. This holds for instances as
much as for modules.
- **[M]** The language cannot enforce this. The convention **is** the rule, and the
  absence of enforcement is not permission. In Python, type checkers do not
  treat the underscore as protected -- do not rely on one to notice.
- **[M]** If an outside caller needs different behaviour, that is a signal to discuss
  a **public** interface change -- never a reason to reach across the
  boundary, and never a reason to add a public wrapper as a workaround.
- **[G]** Inside one module, one object reaching into another object's private members
  is poor practice rather than a boundary violation: prefer not to, and give
  the other object a public method when the need is real.
- *Test:* does the name begin with an underscore, and live in a different
  module from the one using it?

**B4. [M] Every object has one owner; mutation is the owner's to initiate.** An
object is owned by exactly one module, and only that module may change it on
its own initiative.
- **[M]** The owner may **request** another module to change its object -- sorting an
  array, filling a buffer. The request is the call: the mutation happens
  during it, at the owner's initiative, and ends with it. The contract is
  stated in the parameter's type -- a mutable type (`MutableSequence`, `list`,
  `bytearray`) where the callee will change the value, a read-only type
  (`Sequence`, `Mapping`) where it will not. This is the C++ non-const
  reference contract; checkers enforce the read-only side, and the mutable
  side is the statement. **[G]** A name that marks the mutation (`sort_in_place`) is
  welcome where the type cannot say it.
- **[M]** Across a thread boundary nothing mutable is shared: a value is immutable, or
  handed over outright with the giver keeping no reference (C1).
- **[M]** A mutable global is not allowed. That claim is B1's, and this rule points at
  it.
- An object changing itself through its own methods is not mutation from
  outside, and is not this rule's business.
- *Test:* who can change this object on its own initiative? Name one module.
  And does a callee's signature say when it will change a value it is given?

**B5. [M] Public boundaries are narrow, and no public behaviour is chosen by a
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
- **[M] The split public functions wrap one private implementation.** When most of
  two behaviours is common, the public functions state the choice and both call
  a private helper that carries the mode. The mode lives where the commonality
  is exploited -- never at a public boundary. A private helper is exempt from
  this rule: it sits behind the split public names, and its callers are close.
- **[M]** When the same group of options travels together across many call sites,
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

**D1. [M] Named sets are enumerations; absence is a sentinel.** A value drawn from
a fixed, small set is an enumeration -- never a bare string, a bare integer,
or `None` standing as a member of the set.
- A bare value fails silently when misspelled -- `"unkown"` travels as a valid
  state forever. An enumeration fails loudly and is discoverable.
- **[G]** When the value is serialized, prefer an enumeration whose values are the
  stored or wire strings, so the representation stays explicit.
- **[M]** `None` is a legitimate "no value" only where it is not a legal domain value.
  When a parameter must distinguish *not passed* from every value that can be
  passed -- `None` included -- the default is a sentinel object of its own,
  compared by identity (in Python, `dataclasses.MISSING` is the model). The
  sentinel belongs to no set: it marks absence.
- **[G]** Many sentinel-default parameters in one signature is itself a smell -- a
  function taking many optional values is often several functions (B5).
- *Test:* is this value one of a known set? If so, name the set. Does this
  marker assert that nothing was passed? If so, is it an object no value can
  equal?

**D2. [M] Errors are explicit.** No bare `except:`, and no handler that swallows an
exception without acting on it or reporting it.
- **[M]** Convert an error at the boundary where you can add meaning; let it propagate
  where you cannot.
- **[M]** The exceptions a function raises are part of its contract. Document them.
- *Test:* if this fails, does anyone find out?

**D3. [M] The public surface is stated, not inferred.** A module's API is the set of
names it declares as public -- documented, and where the language supports it,
declared explicitly (for example, `__all__`) and typed (F1).
- **[M]** A name is not public because it happens to lack a leading underscore; it is
  public because the module says so.
- *Test:* where does this module say what you are allowed to use?

## E. Tests

**E1. [M] A module is testable without starting the application.** A module's
behaviour can be exercised by calling it directly -- no program launch, no
server, no user interface.
- **[M]** A test that must start the application in order to reach a module is evidence
  that the module's dependencies are not injected. Fix the seam, not the test.
- *Test:* can this module be tested with the program not running?

**E2. [M] Tests are scoped to the unit under test.** Keep module-scope tests (one
module, its collaborators replaced) separate from integration tests (several
modules, or the whole program, wired together).
- Mixing both in one place makes a single module change fan out into the
  integration suite, and a failure no longer tells you which layer is wrong.
- *Test:* when this test fails, does its name tell you whether the unit or the
  assembly broke?

## G. Interfaces

**G1. [M] A module interface is a service or a protocol.** A **service** presents its
capabilities to a general consumer: its interface is its public surface -- the
public functions and methods, and the value types they exchange (D3, F4). A
consumer uses a service as it stands; it implements nothing to do so.
- **[M]** A **protocol** defines one or more **roles** -- what each participant must
  implement to take part -- and takes no role itself. An engine and a user
  interface are roles: the contract between them can be stated without
  implementing either, so either can be replaced without changing the other.
- **[M]** A service may carry a simple callback inline. When the callbacks become roles
  that must be swappable, they are a protocol, and move out (G2).
- *Test:* must a consumer implement something in order to use this interface?
  Then it defines roles, and what it is is a protocol. Does the module act in a
  role it defines? Then it is not a protocol.

**G2. [M] A protocol lives in its own module, and implements no role.** The interface
module contains the role definitions and the values that cross them -- frozen
data classes and enumerations (F4, D1) -- and nothing else.
- **[M]** Role implementations import the protocol module; the protocol module imports
  no role implementation, and role implementations do not import each other.
  Everything one role knows of another is what the protocol states (A1).
- **[M]** The protocol module's documentation follows the same direction: it never
  names or narrates a role implementation (A2).
- In Python a role is stated as a `typing.Protocol` class or an abstract base
  class, and the shared values as frozen data classes and enumerations. Which
  vehicle is a parameter; the separation is the claim.
- *Test:* does this module contain any code that plays a role it defines? Name
  it. And can either role's implementation be replaced without editing the
  other?

## H. Requirements

**H1. [M] Requirements and tests decompose like the design.** Each module has a
requirements doc and a test script that are its own: the requirements doc
states what that module must do, and the test script is the single point of
entry for testing it. A requirement is a claim with one owner (A1) -- the
module it is allocated to.
- The test script may invoke many tests. The claim is that there is one place
  to start testing a module, matching one place to read its requirements.
- **[M]** A new requirement is allocated to a module and documented in **that module's**
  requirements doc -- never in a general list, and never in another module's
  doc (A2).
- The correspondence is the claim; the naming is a parameter -- for example
  `engine.py`, its requirements doc, and `test_engine.py`.
- *Test:* for this requirement, name the module whose doc holds it and the test
  entry point that tests it. If the two answers are not one module, the
  requirement is not allocated.

**H2. [M] A requirement that spans modules decomposes.** When a system requirement
changes multiple modules, it is documented in the system requirements doc as a
**system-level** requirement -- and decomposed into distinct module-level
requirements (H1), each testable at its own module, plus one system test
covering what only the fully integrated system can show.
- **[M]** The system-level doc owns the **composition** -- what the parts must do
  together -- and points at the module requirements rather than restating them
  (A1).
- **[G] Prefer the module level.** Before documenting a system-level requirement,
  ask whether it can be stated at one module; if it can, state it there. A
  requirement that lands on one module is cheaper to state, cheaper to test,
  and cheaper to change. Making requirements land at one module is what the
  decomposition is for.
- **[M]** The system test covers only the composition: what the module tests already
  show is not tested again (E2).
- *Test:* does this requirement name more than one module? Then decompose it --
  name the module requirements, and the single behaviour only integration can
  show. Can it be stated at one module? Then it is a module requirement.

**H3. [M] The decomposition is recursive.** One system requirements doc is the goal.
When the system is too large for a single system requirements doc, the
decomposition gains a level -- top-level, sub-system-level, module-level -- and
the same rules apply at every level.
- **[M]** A sub-system plays the module's part at the level above: its own requirements
  doc, its own single point of test entry (H1), and its own composition to
  state.
- **[M]** A requirement that spans sub-systems is documented and decomposed at the top
  level exactly as H2 handles a requirement that spans modules.
- *Test:* has one requirements doc become a general list? Then the
  decomposition is missing a level, not space.

**H4. [M] Cross-references follow the decomposition downward.** The composition's
doc points at its parts' requirements (H2); a part's doc never points at its
composition. A module's requirements doc does not cite a system-level
requirement, and a sub-system's doc does not cite a system-level doc (H3).
- The reason is reuse: a module whose doc cites the requirement it was built for
  belongs to that system. A module that states only its own claims can be reused
  whole in the next one.
- **[M]** The same discipline holds **within** a level: one part's requirements never
  cite another part's requirements. What two parts share is stated in the
  interface they share -- the protocol (G) -- which belongs to neither of them.
- This is A2's rule given a direction: a claim is documented at the level that
  owns it, and references point downward to what a reader must use -- never
  upward to what occasioned the claim.
- *Test:* does this doc cite anything at a level above its own, or another
  part's claims? Delete the citation, or move the claim to the level that owns
  it.

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

## What this document is not

- It is not a formatting or naming-style guide.
- It describes no tooling and ships no checker.
- It authorizes no refactor, and no cleanup of code that predates it.
- It is not any project's policy, and it does not override a project's own
  conventions.
