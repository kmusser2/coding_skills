---
name: python-naming
description: >
  Python naming: PEP 8 compliance is required, plus the private spellings
  PEP 8 leaves unstated and the PEP 8 corners that are commonly missed --
  names whose constancy and visibility are readable in the name itself.
license: Apache-2.0
compatibility: Requires Python 3.11+
metadata:
  author: kmusser@idi-software.com
  version: "0.1"
---

# Python naming -- portable guidance

**Version:** 0.1 (draft).
**Status:** portable guidance, maintained at the level of the harness and applied
to projects -- it is not part of, and not the policy of, any project it happens to
sit in. If you are reading it inside a project, it is a guest there: that
project's own conventions take precedence.

**Scope.** The spelling of Python names. The conventions are PEP 8's and are
required (N1); this document adds the private spellings PEP 8 leaves unstated
(N2), the enum member spelling PEP 8 never gives (N4), and repeats the PEP 8
corners that are commonly missed (N3). A name the language itself defines
(`__init__` and kin) is spelled as the language spells it.

**Family.** Rule ids are N1--N4 (N for naming), family-wide and stable. The
claims these spellings express -- constancy (B1), privacy (B3), a stated surface
(D3) -- live in the companion skill `modularity`; this document does not restate
them (A1). PEP 8 owns the conventions it states. Typing lives in
`modular-python`; concurrency in `threading`.

## How to apply this

The family conventions -- precedence, scope of application, "principles travel,
parameters do not" -- are stated in the companion skill `modularity` and apply
here unchanged. Each rule ends with a *Test*.

## N. Naming

**N1. Naming follows PEP 8.** The spellings PEP 8 gives for Python names bind
this family: snake_case for functions, methods, variables and parameters,
CamelCase for classes, ALL_CAPS for constants.
- PEP 8 hedges -- "normally", "usually", "consistency within a project is more
  important". This family does not. The convention is the rule; a deviation is
  suppressed with its reason, like any other finding.
- The names state their claims: a constant's case is its constancy (B1), a
  prefix is a name's visibility (B3), a published type reads as a type (D3).
- *Test:* does this name carry the PEP 8 spelling for what it is -- and does
  the spelling match what the name claims?

**N2. The underscore composes with every spelling.** PEP 8 gives the leading
underscore as a weak "internal use" marker, and gives each kind its spelling,
as separate conventions. This family binds both and states the composition:
`_ALL_CAPS` for a private constant, `_CamelCase` for a private class or enum,
`_snake_case` for a private function or method. The marker is not weak here
(B3).
- `_CACHE_TTL_SECONDS = 60`
- `class _ParserState:`, `class _WireFormat(Enum):`
- `def _normalize(text: str) -> str:`, `def _build_parser() -> ArgumentParser:`
- *Test:* does the underscore match who actually reads, calls, or names this?
  If another module does, the name lies (B3).

**N3. The PEP 8 corners that get missed.** PEP 8 owns every claim below (A1).
They are repeated because they are routinely got wrong, and a pointer does not
help a reader who never follows it; where this list and PEP 8 disagree, PEP 8
is right. This list is an index, not a second owner.
- Type variables take short CapWords, preferring one letter -- `T`, `AnyStr`,
  `Proto`-suffixed where a protocol bound is meant -- never `t`, never
  `value_type`.
- An exception class ends in `Error`: `class ParseError(Exception)` -- and is
  CamelCase like any class.
- A name that would collide with a keyword takes a trailing underscore:
  `class_`, `type_` -- never `klass`, never `type1`.
- `__double_leading` is name mangling, not stronger privacy: the language
  rewrites it to `_Class__name` to dodge subclass collisions. Privacy is one
  underscore, and B3 says what it means.
- `__dunder__` names are the language's reserved spelling for its own
  protocols. Never invent one; there is no safe second meaning.
- The single-character names `l`, `O` and `I` are banned: they are not readable
  at a glance (`l` and `1`, `O` and `0`).
- Module names are short and all-lowercase; underscores where they improve
  readability (`xml_reader`, `xmlreader` -- both fine). A **public** package
  name is short, all-lowercase and carries **no** underscores (`xmltools`,
  `netcode`): PEP 8 only discourages them there -- this family prohibits them.
  A **private** package keeps the underscore marker and may separate words
  (`_internal_tools`, `_model_v2`). Never CapWords.
- Undocumented names are internal (PEP 8, "Public and Internal Interfaces") --
  which is D3's claim, and why `__all__` states the surface.
- *Test:* for a name in this list's territory, is this the PEP 8 spelling --
  and did the answer come without opening PEP 8?

**N4. An enum member is ALL_CAPS.** An enum member is a constant scoped to its
class, and takes the constant spelling (N1). PEP 8 does not name enum members at
all -- this rule is additive, not a restatement.
- `class Status(StrEnum): QUEUED = "queued"` -- the name is the constant's
  spelling, the value is the wire form (D1). Both are stated.
- A member the language defines (`_missing_`, `_generate_next_value_`,
  `_ignore_`) is spelled as the language spells it.
- *Test:* would this member be a constant at module scope? Then it takes the
  constant's spelling.

## Examples

**A name states its claim (N1--N2).**
- `maxRetries = 3` states nothing: constant or mutable? private or published?
  The reader must open the module to find out. `MAX_RETRIES` and `_MAX_RETRIES`
  state both at a glance -- constancy in the case, visibility in the prefix.
- `class job:`, `class _status:`, `def ParseText():` and `def parseText():` mix
  the axes, or announce another language's habits. Each axis has one spelling:
  CamelCase, ALL_CAPS, snake_case -- and an underscore prefix for what is
  nobody else's business.

## What this document is not

- It is not a copy of PEP 8. Where a PEP 8 claim appears here, PEP 8 owns it
  (A1); N3 repeats its commonly-missed corners deliberately, as an index -- that
  is its whole function.
- It restates no principle that the `modularity` skill owns (A1).
- It is not any project's policy, and it does not override a project's own
  conventions.
