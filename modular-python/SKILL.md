---
name: modular-python
description: >
  Python typing rules for modular design -- annotations, `Any`, generics,
  value shapes -- the Python expression of the language-independent modularity
  skill.
license: Apache-2.0
compatibility: Requires Python 3.11+
metadata:
  author: kmusser@idi-software.com
  version: "0.1"
---

# Python types and value shapes -- portable guidance

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

**Scope.** The Python expression of the modularity principles: how Python's
typing states the contracts those principles require. The principles are
language-independent and live in the companion skill `modularity`; the
concurrency rules live in the companion skill `threading`. This document
states F1--F4 and points at the principles rather than restating them (A1).
Rule ids are family-wide and stable.

## How to apply this

The family conventions -- precedence, scope of application, "principles travel,
parameters do not" -- are stated in the companion skill `modularity` and apply
here unchanged. Each rule ends with a *Test*.

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

**An enum or a frozen data class (F4).**
- `Status` is one of `QUEUED`, `RUNNING`, `DONE` -- one value from a named set:
  `Status` is an enumeration. The member names are constants (N4); the values
  are the wire strings (D1): `QUEUED = "queued"`.
- `Job(id=7, owner="ada", status=Status.QUEUED)` is several named facts
  travelling together: `Job` is a frozen data class, and its `status` field is
  the enum.
- `{"id": 7, "status": "queued"}` is the same claim with no owner -- a bare dict
  (F3) around a bare string (D1). When the facts are one-of-a-set, the shape is
  an enum; when they are several named values, it is a class.

## What this document is not

- It is not a formatting or naming-style guide.
- It restates no principle that the `modularity` skill owns (A1).
- It describes no tooling beyond the reference checker placeholder in
  `scripts/`; enforcement belongs to the project.
- It is not any project's policy, and it does not override a project's own
  conventions.
