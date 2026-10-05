"""check_modularity.py -- reference checker for the modularity and
modular-python skills.

STATUS: PLACEHOLDER. Structure only -- no checks are implemented yet. The
planned checks below are the reviewed tier structure; implementations land
after the principles are settled.

Purpose
-------
Mechanically check the family rules (modularity/SKILL.md and ../SKILL.md) that
are marked machine-checkable, so compliance is a tool's verdict rather than a
reviewer's judgement: "mechanical rules are checked, not reasoned about".

Design contract
---------------
- Each implemented check carries the id of the rule it enforces. A meta-test
  asserts that this file's implemented ids match the rules marked *Check:* in
  the skill docs (A1: this file is a derived owner, never a second author).
- Stdlib only, single file, no dependencies. (Tier 2 config is read from
  `[tool.check_modularity]` in pyproject.toml via `tomllib`.)
- Suppression: a `# modularity: allow <reason>` comment on the offending line.
  The reason is mandatory; a bare `allow` is itself a finding.
- Output: `path:line:col: [RULE] message`; exit 1 on any finding, else 0.

Tier 1 -- implement first (decidable by AST/regex, low false-positive rate).
Tier 2 -- mechanizable but needs project config (naming/id conventions) or
  tolerates heuristic noise: warning-grade, suppression-friendly.
Tier 3 -- judgement only. Never checked here; the *Test:* question in the rule
  is the instrument. Listed so the meta-test knows what NOT to expect.

Usage (once implemented):

    python scripts/check_modularity.py path/to/code...
"""

TIER1_CHECKS: tuple[tuple[str, str], ...] = (
    ("B1", "module-scope state: mutable literal bindings, `global`, `globals()`"),
    ("B2", "loading does no work: module-scope `with`, bare calls, banned families"),
    ("A2", "no locations in documentation (paths, `.py`, `line N`)"),
    ("D2", "errors are explicit: no bare `except:`, no swallow without report"),
    ("D3", "the public surface is stated: `__all__` present and complete"),
    ("F1", "public functions/methods annotated (parameters + return)"),
    ("F2", "no `Any` in annotations"),
    ("F3", "containers name what they hold (no bare generics)"),
    ("F4", "public signatures carry named-field values (no bare dict / wide tuple)"),
)

TIER2_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("H1", "per module: one requirements doc and one test entry point exist",
     "naming templates per project"),
    ("H4", "cross-references flow downward: no citations above or beside a level",
     "requirement-id convention"),
    ("B4", "declared mutation: no mutation of read-only typed parameters",
     "heuristic: stashing a loan"),
    ("B3", "privacy: no `x._y` outside `self`/`cls`/`super()`",
     "heuristic: module-internal access is discouraged, not forbidden"),
    ("G2", "protocol purity: interface modules contain no role implementation",
     "heuristic: protocol modules detected by stub-only roles"),
)

JUDGEMENT_ONLY: tuple[tuple[str, str], ...] = (
    ("A1", "ownership of claims -- a dedupe detector would contradict the rule"),
    ("B5", "mode vs option flag -- the 'or'-test beats the AST heuristic"),
    ("D1", "magic values -- string heuristics too noisy"),
    ("E1", "testable without the application"),
    ("E2", "test layers scoped"),
    ("G1", "service vs protocol -- classification"),
    ("H2", "decomposition of a spanning requirement"),
    ("H3", "recursive levels"),
    ("C1", "-- deferred with the threading skill (C1--C5)"),
)


def main(argv: list[str] | None = None) -> int:
    """Report planned coverage by tier; check nothing until rules are settled."""
    print("check_modularity.py: PLACEHOLDER -- no checks implemented yet.")
    print()
    print("Tier 1 -- implement first (decidable, low noise):")
    for rule_id, claim in TIER1_CHECKS:
        print(f"  {rule_id}  {claim}")
    print()
    print("Tier 2 -- mechanizable with config or heuristics (warning-grade):")
    for rule_id, claim, needs in TIER2_CHECKS:
        print(f"  {rule_id}  {claim}  [needs: {needs}]")
    print()
    print("Tier 3 -- judgement only (never checked here):")
    for rule_id, why in JUDGEMENT_ONLY:
        print(f"  {rule_id}  {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
