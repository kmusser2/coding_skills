#!/usr/bin/env python3
# TYPE: TOOLKIT
# keywords: |python|modularity|naming|check|rules|enforce|style|compliance|skill|
# examples: |import python; python.check_modularity()|import python; python.check_naming('src')|import python; python.plan()|
# modularity: allow the docstring names the module and states output patterns to give the tool's contract; those are names and pattern texts, not location references (A1)
"""python.py - enforce the modularity and naming coding skills

Python API (importable from any python_eval call):
  import python
  python.check_modularity()        -> findings for the modularity family rules
  python.check_naming()            -> findings for the naming rules
  python.check_all()               -> both checkers, merged and sorted
  python.plan()                    -> what is checked, and what is judgement-only
  python.format_findings(findings) -> "path:line:col: [RULE] message" lines
  python.ok(findings)              -> True when a run is clean

A Finding is (path, line, col, rule, message); the rule id names a rule in
the companion skills, which own the claim. A clean run is a verdict on the
machine-checkable rules alone -- plan() lists what remains judgement.

Suppression: `# modularity: allow <reason>` on the flagged line or the line
above; the reason is mandatory.

CLI:
  python toolkit/python/__init__.py --selftest   # contract and smoke tests for this tool
"""

__all__ = ["VERSION", "Finding", "RuleTable", "Plan", "check_modularity",
           "check_naming", "check_all", "plan", "format_findings", "ok", "main"]

import argparse
import importlib.util
import os
import tempfile
from collections.abc import Container, Iterable, Sequence
from functools import lru_cache
from types import ModuleType
from typing import NamedTuple

VERSION: str = "0.1"


class Finding(NamedTuple):
    """One rule finding: the source location, the rule id, and what the checker saw."""
    path: str
    line: int
    col: int
    rule: str
    message: str


class RuleTable(NamedTuple):
    """One checker's rule rows, grouped by status: checked now, planned, and judgement-only."""
    checked: tuple[tuple[str, ...], ...]
    planned: tuple[tuple[str, ...], ...]
    judgement: tuple[tuple[str, ...], ...]


class Plan(NamedTuple):
    """Both checkers' rule tables: what a clean run does and does not vouch for."""
    modularity: RuleTable
    naming: RuleTable


@lru_cache(maxsize=None)
def _helper(name: str) -> ModuleType:
    """Load a checker helper that lives beside this tool (lazy, cached)."""
    location = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
    spec = importlib.util.spec_from_file_location(name, location)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load checker helper {name!r}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adopt(raw: Iterable[object]) -> Finding:
    """Normalize a helper's finding record into this tool's Finding shape."""
    return Finding._make(raw)


def _as_paths(paths: str | Sequence[str] | None) -> list[str]:
    """Normalize a path argument: None means the current directory."""
    if paths is None:
        return ["."]
    if isinstance(paths, str):
        return [paths]
    return list(paths)


def check_modularity(paths: str | Sequence[str] | None = None, *,
                     exclude: Container[str] = ()) -> list[Finding]:
    """Check Python sources against the modularity family rules (B, A, D, F).

    Returns the findings sorted by location. `exclude` names rule ids the
    project has excluded (the Exclusions convention of the modularity skill).
    """
    findings = (_adopt(item)
                for item in _helper("check_modularity").run(_as_paths(paths)))
    return sorted(f for f in findings if f.rule not in set(exclude))


def check_naming(paths: str | Sequence[str] | None = None, *,
                  exclude: Container[str] = ()) -> list[Finding]:
    """Check Python sources against the naming rules (N).

    Returns the findings sorted by location. `exclude` names rule ids the
    project has excluded (the Exclusions convention of the modularity skill).
    """
    findings = (_adopt(item)
                for item in _helper("check_naming").run(_as_paths(paths)))
    return sorted(f for f in findings if f.rule not in set(exclude))


def check_all(paths: str | Sequence[str] | None = None, *,
               exclude: Container[str] = ()) -> list[Finding]:
    """Run both checkers over the same paths and merge their findings."""
    return sorted(check_modularity(paths, exclude=exclude)
                  + check_naming(paths, exclude=exclude))


def plan() -> Plan:
    """The rule tables behind both checkers, grouped by status: checked now,
    planned, and judgement-only. A clean run is a verdict on the checked rules
    alone; the judgement rules rest on the Test questions in the skills."""
    modularity = _helper("check_modularity")
    naming = _helper("check_naming")
    return Plan(
        modularity=RuleTable(
            checked=tuple(modularity.TIER1_CHECKS),
            planned=tuple(modularity.TIER2_CHECKS),
            judgement=tuple(modularity.JUDGEMENT_RULES)),
        naming=RuleTable(
            checked=tuple(naming.COVERAGE),
            planned=(),
            judgement=()))


def format_findings(findings: Sequence[Finding]) -> list[str]:
    """Render findings as report lines, each `path:line:col: [RULE] message`."""
    return [f"{f.path}:{f.line}:{f.col}: [{f.rule}] {f.message}" for f in findings]


def ok(findings: Sequence[Finding]) -> bool:
    """True when the finding list is empty: a clean run."""
    return not findings


def _selftest() -> int:
    """Contract and smoke tests: helper wiring, finding shape, known findings."""
    passed = True

    def check(name: str, condition: bool) -> None:
        nonlocal passed
        passed = passed and condition
        print(("PASS" if condition else "FAIL") + "  " + name)

    good = ('"""Fixture: a compliant module."""\n'
            '__all__ = ["double"]\n'
            '\n'
            'def double(value: int) -> int:\n'
            '    """Return the value doubled."""\n'
            '    return value * 2\n')
    bad = ('def Bad():\n'
           '    return 1\n')
    with tempfile.TemporaryDirectory() as work:
        for name, source in (("good_mod.py", good), ("bad_mod.py", bad)):
            with open(os.path.join(work, name), "w", encoding="utf-8") as handle:
                handle.write(source)
        clean = check_all(os.path.join(work, "good_mod.py"))
        dirty = check_all(os.path.join(work, "bad_mod.py"))
        rules = {f.rule for f in dirty}
        check("a compliant fixture passes both checkers", ok(clean))
        check("violations are found and carry rule ids", {"D3", "F1", "N1"} <= rules)
        check("findings honor the contract shape",
              all(isinstance(f, Finding) and len(f) == 5 for f in dirty))
        check("format renders report lines",
              all(line.count(":") >= 3 for line in format_findings(dirty)))
        check("ok() reports cleanliness", ok(clean) and not ok(dirty))
    print()
    print("ALL TESTS PASSED" if passed else "SOME TESTS FAILED")
    return 0 if passed else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry: check paths (default: the current directory) or run self tests."""
    parser = argparse.ArgumentParser(
        prog="python",
        description="check Python sources against the Python coding skills")
    parser.add_argument("paths", nargs="*", help="files or directories to check")
    parser.add_argument("--selftest", action="store_true", help="run the tool's self tests")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    findings = check_all(args.paths or None)
    for line in format_findings(findings):
        print(line)
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
