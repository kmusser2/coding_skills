# Copyright (c) 2026 kmusser@idi-software.com
# SPDX-License-Identifier: MIT
# modularity: allow the docstring quotes names and patterns to state the checker's contract; those are pattern texts, not location references (A1)
"""check_modularity.py -- reference checker for the modularity and
modular-python skills.

STATUS: Tier 1 implemented; Tier 2 and Tier 3 remain planned (see the tables
below). The principles are still settling, so implementations land per tier.

Purpose
-------
Mechanically check the family rules (modularity/SKILL.md and the local
SKILL.md) that are marked machine-checkable, so compliance is a tool's verdict
rather than a reviewer's judgement: "mechanical rules are checked, not
reasoned about".

Design contract
---------------
- Each check carries the id of the rule it enforces. A meta-test asserts that
  the implemented ids match the rules marked *Check:* in the skill docs (A1:
  this file is a derived owner, never a second author).
- Stdlib only, single file, no dependencies. Tier 2 config will be read from
  `[tool.check_modularity]` in the project's pyproject file via `tomllib`.
- Suppression: a `# modularity: allow <reason>` comment on the flagged line or
  the line above. The reason is mandatory; a bare `allow` is itself a finding.
- Output: `path:line:col: [RULE] message`. Exit 1 on any finding, else 0.

Tier 1 (implemented below): decidable by AST/regex, low false-positive rate.
Tier 2 (planned): mechanizable but needs project config or tolerates heuristic
noise -- warning-grade, suppression-friendly.
Tier 3 (never checked): judgement only; the *Test:* question in the rule is
the instrument. Listed so the meta-test knows what to expect.

Scope notes for Tier 1:
- A2's check covers the locations half of the rule only.
- F4's check covers the signature-shapes half; bare generics are F3's.
- `__all__` is exempt from B1: it is Python's declared-surface registry, built
  at import (B2's carveout) and read-only thereafter.
- Code under `if __name__ == '__main__':` or `if TYPE_CHECKING:` does not run
  at import and is not scanned by B2.
- F1 exempts names beginning with underscore (private and dunder alike) and
  nested functions (not module surface).

Usage:

    python scripts/check_modularity.py [path ...]     # default: current dir
    python scripts/check_modularity.py --plan         # print the tier tables
"""

__all__ = ["TIER1_CHECKS", "TIER2_CHECKS", "JUDGEMENT_RULES", "main"]

import argparse
import ast
import os
import re
import sys
import tokenize
from typing import NamedTuple

TIER1_CHECKS: tuple[tuple[str, str], ...] = (
    ("B1", "module-scope state: mutable literal bindings, `global`, `globals()`"),
    ("B2", "loading does no work: module-scope `with`, bare calls, banned families"),
    ("A2", "no locations in documentation (paths, file names, line numbers)"),
    ("D2", "errors are explicit: no bare `except:`, no swallow without report"),
    ("D3", "the public surface is stated: `__all__` present and complete"),
    ("F1", "public functions/methods annotated (parameters + return)"),
    ("F2", "no `Any` in annotations"),
    ("F3", "containers name what they hold (no bare generics)"),
    ("F4", "public signatures carry named-field values (no dict / wide tuple)"),
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

JUDGEMENT_RULES: tuple[tuple[str, str], ...] = (
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

# --- vocabulary the checks match against -----------------------------------

MUTABLE_BUILDERS: frozenset[str] = frozenset(
    {"list", "dict", "set", "bytearray", "deque", "Counter",
     "defaultdict", "OrderedDict"})
MUTABLE_DISPLAYS = (ast.List, ast.Dict, ast.Set, ast.ListComp,
                    ast.DictComp, ast.SetComp)

BARE_GENERICS: frozenset[str] = frozenset(
    {"dict", "list", "set", "frozenset", "tuple", "type",
     "Dict", "List", "Set", "FrozenSet", "Tuple", "Type",
     "Callable", "Iterable", "Iterator", "Sequence", "Mapping",
     "MutableMapping", "MutableSequence", "AbstractSet", "Generator",
     "Deque", "Counter", "DefaultDict", "OrderedDict", "Pattern", "Match"})

DICT_FAMILY: frozenset[str] = frozenset({"dict", "Dict"})
TUPLE_FAMILY: frozenset[str] = frozenset({"tuple", "Tuple"})

WORK_CALLS: frozenset[str] = frozenset(
    {"open", "print", "input", "exec", "eval"})
WORK_CALL_PREFIXES: tuple[str, ...] = (
    "signal.signal", "logging.basicConfig", "os.system", "os.remove",
    "os.rename", "subprocess.", "requests.", "socket.", "urllib.",
    "http.client", "ftplib.", "smtplib.")

_SWALLOW_BODY = (ast.Pass, ast.Break, ast.Continue)

_SUPPRESS_RE = re.compile(r"#\s*modularity:\s*allow\s+(\S.*?)\s*$")
_ALLOW_BLANK_RE = re.compile(r"#\s*modularity:\s*allow\s*$")
_LOCATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\w.~-]*[./][\w.~-]*:\d+\b"),   # file:line (most specific first)
    re.compile(r"[A-Za-z]:\\"),                    # windows path
    re.compile(r"(?:[\w.~-]+/)+[\w.~-]+\.\w+"),  # path/with/suffix.ext
    re.compile(r"(?<![\w.])line\s+\d+", re.IGNORECASE),
    re.compile(r"\.py\b"),
)
_URL_RE = re.compile(r"\S*://\S+")
_TEST_FILE_RE = re.compile(r"(^test_)|(_test\.py$)")


class _Finding(NamedTuple):
    path: str
    line: int
    col: int
    rule: str
    message: str


def _root_name(node: ast.expr) -> str:
    """Name of the outermost symbol of an annotation, or ''."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _dotted(node: ast.expr) -> str:
    """Dotted name of a call target, or ''."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def _is_main_guard(test: ast.expr) -> bool:
    return (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and any(isinstance(c, ast.Constant) and c.value == "__main__"
                    for c in test.comparators))


def _is_type_checking(test: ast.expr) -> bool:
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def _module_scope(tree: ast.Module) -> list[ast.stmt]:
    """Statements that run at import time in module scope (not in defs/classes)."""
    out: list[ast.stmt] = []
    stack: list[ast.stmt] = list(reversed(tree.body))
    while stack:
        node = stack.pop()
        out.append(node)
        if isinstance(node, ast.If):
            if _is_main_guard(node.test) or _is_type_checking(node.test):
                continue
            stack.extend(reversed(node.body + node.orelse))
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            stack.extend(reversed(node.body + node.orelse))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            stack.extend(reversed(node.body))
        elif isinstance(node, ast.Try):
            nested = list(node.body) + list(node.orelse) + list(node.finalbody)
            for handler in node.handlers:
                nested.extend(handler.body)
            stack.extend(reversed(nested))
        elif isinstance(node, ast.Match):
            nested = []
            for case in node.cases:
                nested.extend(case.body)
            stack.extend(reversed(nested))
    return out


def _binding_names(node: ast.stmt) -> list[str]:
    """Names bound by one module-scope statement."""
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        return [node.target.id] if isinstance(node.target, ast.Name) else []
    if isinstance(node, ast.For):
        return [t.id for t in ast.walk(node.target) if isinstance(t, ast.Name)]
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        names = []
        for alias in node.names:
            names.append(alias.asname or alias.name.split(".")[0])
        return names
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    return []

# --- checks -----------------------------------------------------------------

def _is_mutable_value(value: ast.expr) -> bool:
    if isinstance(value, MUTABLE_DISPLAYS):
        return True
    return (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id in MUTABLE_BUILDERS)


def _check_b1(tree: ast.Module, module_stmts: list[ast.stmt], path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    bind_sites: dict[str, list[int]] = {}
    for stmt in module_stmts:
        for name in _binding_names(stmt):
            bind_sites.setdefault(name, []).append(stmt.lineno)
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            value = stmt.value
            targets = (stmt.targets if isinstance(stmt, ast.Assign)
                       else [stmt.target])
            for target in targets:
                if (isinstance(target, ast.Name) and target.id != "__all__"
                        and value is not None and _is_mutable_value(value)):
                    findings.append(_Finding(path, stmt.lineno, stmt.col_offset + 1,
                        "B1", f"module-level name '{target.id}' is bound to a mutable "
                              "value; bind an immutable one, move the state into an "
                              "object, or suppress with its reason if this is a "
                              "registration registry built at import (B1 carveout)"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                "B1", f"'global {', '.join(node.names)}': state that changes after "
                      "start-up belongs to an object, not to a module"))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "globals"):
            findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                "B1", "globals() reaches into module state; move the state into an "
                      "object"))
    for name, sites in sorted(bind_sites.items()):
        if len(sites) > 1:
            findings.append(_Finding(path, sites[1], 1, "B1",
                f"module-level name '{name}' is bound {len(sites)} times "
                f"(lines {', '.join(str(s) for s in sites)}); a constant is bound once"))
    return findings


def _check_b2(tree: ast.Module, module_stmts: list[ast.stmt], path: str) -> list[_Finding]:
    findings: list[_Finding] = []

    def work_call(call: ast.Call) -> bool:
        dotted = _dotted(call.func)
        return (dotted in WORK_CALLS
                or any(dotted.startswith(p) for p in WORK_CALL_PREFIXES))

    for stmt in module_stmts:
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            findings.append(_Finding(path, stmt.lineno, stmt.col_offset + 1,
                "B2", "loading a module performs I/O: `with` at module scope; move "
                      "the work behind a call"))
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue  # a definition runs at import only in its decorator; bodies do not run
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and work_call(node):
                findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                    "B2", f"loading a module calls '{_dotted(node.func)}'; I/O and "
                          "process work belong behind a call"))
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            if not work_call(stmt.value):
                findings.append(_Finding(path, stmt.lineno, stmt.col_offset + 1,
                    "B2", f"loading a module calls '{_dotted(stmt.value.func) or '<expr>'}'; "
                          "declarative registration binds a value -- bare calls are work"))
    return findings


def _docstrings(tree: ast.Module) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef,
                             ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.append((body[0].lineno, body[0].value.value))
    return out


def _check_a2(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    for line, doc in _docstrings(tree):
        scrubbed = _URL_RE.sub(" ", doc)
        seen_spans: list[tuple[int, int]] = []
        for pattern in _LOCATION_RES:
            for match in pattern.finditer(scrubbed):
                span = match.span()
                if any(span[0] < s[1] and s[0] < span[1] for s in seen_spans):
                    continue
                seen_spans.append(span)
                findings.append(_Finding(path, line, 1, "A2",
                    f"documentation names a location: {match.group(0)!r} -- point at "
                    "a public name instead"))
    return findings


def _is_swallow_body(body: list[ast.stmt]) -> bool:
    for stmt in body:
        if isinstance(stmt, _SWALLOW_BODY):
            continue
        if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is Ellipsis):
            continue
        return False
    return bool(body)


def _check_d2(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            continue
        for handler in node.handlers:
            if handler.type is None:
                findings.append(_Finding(path, handler.lineno, handler.col_offset + 1,
                    "D2", "bare 'except:' catches everything; name the exception"))
            elif _is_swallow_body(handler.body):
                findings.append(_Finding(path, handler.lineno, handler.col_offset + 1,
                    "D2", "handler swallows the exception without acting on it or "
                          "reporting it"))
    return findings


def _check_d3(tree: ast.Module, module_stmts: list[ast.stmt], path: str) -> list[_Finding]:
    basename = os.path.basename(path)
    if basename.startswith("_") or _TEST_FILE_RE.search(basename):
        return []
    findings: list[_Finding] = []
    declared: list[str] | None = None
    for stmt in module_stmts:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "__all__"
                and isinstance(stmt.value, (ast.List, ast.Tuple, ast.Set))):
            declared = [e.value for e in stmt.value.elts
                        if isinstance(e, ast.Constant)
                        and isinstance(e.value, str)]
    if declared is None:
        findings.append(_Finding(path, 1, 1, "D3",
            "public module states no `__all__`; the surface must be declared, not "
            "inferred"))
        return findings
    bound = {name for stmt in module_stmts for name in _binding_names(stmt)}
    for name in declared:
        if name not in bound:
            findings.append(_Finding(path, 1, 1, "D3",
                f"'{name}' is listed in `__all__` but not defined"))
    return findings


def _surface_funcs(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def walk_body(body: list[ast.stmt]) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(stmt)
            elif isinstance(stmt, ast.ClassDef):
                walk_body(stmt.body)

    walk_body(tree.body)
    return out


def _iter_annotations(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and node.annotation is not None:
            yield node.annotation
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))                 and node.returns is not None:
            yield node.returns
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            yield node.annotation


def _check_f1(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    for func in _surface_funcs(tree):
        if func.name.startswith("_"):
            continue
        missing: list[str] = []
        positional = list(func.args.posonlyargs) + list(func.args.args)
        for i, arg in enumerate(positional):
            if i == 0 and arg.arg in ("self", "cls"):
                continue
            if arg.annotation is None:
                missing.append(arg.arg)
        for arg in (func.args.vararg, func.args.kwarg):
            if arg is not None and arg.annotation is None:
                missing.append(arg.arg)
        for arg in func.args.kwonlyargs:
            if arg.annotation is None:
                missing.append(arg.arg)
        if func.returns is None:
            missing.append("return")
        if missing:
            findings.append(_Finding(path, func.lineno, func.col_offset + 1, "F1",
                f"public function '{func.name}' is untyped: "
                f"missing {', '.join(missing)}"))
    return findings


def _check_f2(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    for annotation in _iter_annotations(tree):
        for node in ast.walk(annotation):
            if (isinstance(node, ast.Name) and node.id == "Any") or (
                    isinstance(node, ast.Attribute) and node.attr == "Any"):
                findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                    "F2", "'Any' turns off checking here and everywhere it spreads; "
                          "annotate 'object' and narrow, or suppress at a named "
                          "carveout with its reason"))
    return findings


def _check_f3(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []
    for annotation in _iter_annotations(tree):
        if isinstance(annotation, ast.Subscript):
            continue
        name = _root_name(annotation)
        if name in BARE_GENERICS:
            findings.append(_Finding(path, annotation.lineno, annotation.col_offset + 1,
                "F3", f"bare '{name}' is dict[Any, Any] in different clothes; "
                      "parameterize the generic"))
    return findings


def _check_f4(tree: ast.Module, path: str) -> list[_Finding]:
    findings: list[_Finding] = []

    def flag(annotation: ast.expr, what: str, name: str) -> None:
        findings.append(_Finding(path, annotation.lineno, annotation.col_offset + 1,
            "F4", f"{what} carries a {name} across a public boundary; give the value "
                  "named fields"))

    for func in _surface_funcs(tree):
        if func.name.startswith("_"):
            continue
        sites = [a.annotation for a in
                 list(func.args.posonlyargs) + list(func.args.args)
                 + list(func.args.kwonlyargs)
                 + [a for a in (func.args.vararg, func.args.kwarg) if a]
                 if a.annotation is not None]
        if func.returns is not None:
            sites.append(func.returns)
        for annotation in sites:
            root = annotation.value if isinstance(annotation, ast.Subscript) else annotation
            name = _root_name(root)
            if name in DICT_FAMILY:
                flag(annotation, "a parameter or return", "dict")
            elif name in TUPLE_FAMILY and isinstance(annotation, ast.Subscript):
                elts = annotation.slice.elts if isinstance(annotation.slice, ast.Tuple) else []
                wide = len(elts) >= 2 and not any(
                    isinstance(e, ast.Constant) and e.value is Ellipsis for e in elts)
                if wide:
                    flag(annotation, "a parameter or return",
                         f"tuple of {len(elts)}")
    return findings


# --- suppression and driver -------------------------------------------------

def _read_suppressions(path: str) -> tuple[dict[int, str], list[_Finding]]:
    suppress: dict[int, str] = {}
    findings: list[_Finding] = []
    try:
        with tokenize.open(path) as handle:
            tokens = list(tokenize.generate_tokens(handle.readline))
    except (OSError, SyntaxError, tokenize.TokenError):
        return suppress, findings
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        blank = _ALLOW_BLANK_RE.search(token.string)
        allowed = _SUPPRESS_RE.search(token.string)
        if allowed:
            suppress[line] = allowed.group(1)
        elif blank:
            findings.append(_Finding(path, line, token.start[1] + 1, "SUP",
                "suppression without a reason; write `# modularity: allow <reason>`"))
    return suppress, findings


def _check_file(path: str) -> list[_Finding]:
    try:
        with tokenize.open(path) as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)
    except (OSError, SyntaxError) as exc:
        return [_Finding(path, 1, 1, "PARSE", f"cannot parse: {exc}")]
    suppress, findings = _read_suppressions(path)
    module_stmts = _module_scope(tree)
    for check in (_check_b1, _check_b2, _check_a2, _check_d2):
        findings.extend(check(tree, module_stmts, path) if check in
                        (_check_b1, _check_b2) else check(tree, path))
    findings.extend(_check_d3(tree, module_stmts, path))
    for check in (_check_f1, _check_f2, _check_f3, _check_f4):
        findings.extend(check(tree, path))
    return [f for f in findings
            if f.line not in suppress and (f.line - 1) not in suppress]


def _iter_py_files(paths: list[str]):
    for given in paths:
        if os.path.isfile(given):
            if given.endswith(".py"):
                yield given
            continue
        for root, dirs, files in os.walk(given):
            dirs[:] = sorted(d for d in dirs
                             if not d.startswith(".") and d != "__pycache__")
            for name in sorted(files):
                if name.endswith(".py"):
                    yield os.path.join(root, name)


def _print_plan() -> None:
    print("Tier 1 -- implemented:")
    for rule_id, claim in TIER1_CHECKS:
        print(f"  {rule_id}  {claim}")
    print()
    print("Tier 2 -- planned (config or heuristics, warning-grade):")
    for rule_id, claim, needs in TIER2_CHECKS:
        print(f"  {rule_id}  {claim}  [needs: {needs}]")
    print()
    print("Tier 3 -- judgement only (never checked):")
    for rule_id, why in JUDGEMENT_RULES:
        print(f"  {rule_id}  {why}")


def main(argv: list[str] | None = None) -> int:
    """Check Python files against the Tier 1 rules; 1 on findings, else 0."""
    parser = argparse.ArgumentParser(
        prog="check_modularity",
        description="reference checker for the modularity skill family (Tier 1)")
    parser.add_argument("paths", nargs="*", default=["."],
                        help="files or directories to check (default: current dir)")
    parser.add_argument("--plan", action="store_true",
                        help="print the tier tables and exit")
    args = parser.parse_args(argv)
    if args.plan:
        _print_plan()
        return 0
    findings: list[_Finding] = []
    for file_path in _iter_py_files(args.paths or ["."]):
        findings.extend(_check_file(file_path))
    for finding in sorted(findings):
        print(f"{finding.path}:{finding.line}:{finding.col}: "
              f"[{finding.rule}] {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
