# modularity: allow the docstring quotes the script name and usage; pattern text, not a location reference (A1)
"""check_naming.py -- reference checker for the python-naming skill.

SCOPE: this checker implements the python-naming skill (N1--N4) and nothing
else. It deliberately shares no checks with check_modularity.py: a project may
use either skill -- and either checker -- alone. Nothing here reclaims a claim
that belongs to the other family.

STATUS: implemented. The partial and judgement-only corners of N3 are listed
below and are not checked.

Design contract (the family's, unchanged):
- Each check carries the id of the rule it enforces.
- Stdlib only, single file, no dependencies.
- Suppression: `# naming: allow <reason>` on the flagged line or the line
  above. The family form `# modularity: allow <reason>` is accepted too. The
  reason is mandatory; a bare `allow` is itself a finding.
- Output: `path:line:col: [RULE] message`; exit 1 on any finding, else 0.

Coverage:
  N1  public spellings: snake_case functions, methods, variables and
      parameters; CamelCase classes; ALL_CAPS constants
  N2  the underscore composition: _snake_case, _CamelCase, _ALL_CAPS
  N3  the PEP 8 corners: type variables, exception `Error` suffix, common
      keyword evasions (partial), no invented dunders, `l`/`O`/`I` banned,
      module and package names (public packages: no underscores)
  N4  enum members are ALL_CAPS

Not checked here:
- whether a module-level name is truly a constant -- the value claim is B1's
  in the modularity skill, and this checker will not claim it. A literal value
  is treated as a constant for spelling purposes; anything else accepts either
  spelling.
- `__double_leading` mangling semantics and "undocumented is internal"
  (knowledge, not detection).
- the trailing-underscore keyword rule in full; only the common evasions are
  flagged.

Usage:

    python scripts/check_naming.py [path ...]     # default: current dir
    python scripts/check_naming.py --plan
"""

__all__ = ["COVERAGE", "main"]

import argparse
import ast
import os
import re
import sys
import tokenize
from typing import NamedTuple

COVERAGE: tuple[tuple[str, str], ...] = (
    ("N1", "PEP 8 spellings bind: snake_case, CamelCase, ALL_CAPS"),
    ("N2", "the underscore composes: _snake_case, _CamelCase, _ALL_CAPS"),
    ("N3", "the PEP 8 corners that get missed"),
    ("N4", "enum members are ALL_CAPS"),
)

FUNC_RE = re.compile(r"^_?[a-z][a-z0-9_]*$")
CLASS_RE = re.compile(r"^_?[A-Z][A-Za-z0-9]*$")
CONST_RE = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
NAME_RE = re.compile(r"^(_?[A-Z][A-Z0-9_]*|_?[a-z][a-z0-9_]*)$")
MODULE_RE = re.compile(r"^_?[a-z][a-z0-9_]*$")
PKG_PUBLIC_RE = re.compile(r"^[a-z][a-z0-9]*$")
PKG_PRIVATE_RE = re.compile(r"^_[a-z][a-z0-9_]*$")
_ENUM_BASE_RE = re.compile(r"(Enum|Flag)$")
_EXCEPTION_BASE_RE = re.compile(r"(Exception|Error)$")
_TYPEVAR_BASES: frozenset[str] = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})
AMBIGUOUS: frozenset[str] = frozenset({"l", "O", "I"})
KEYWORD_EVASIONS: frozenset[str] = frozenset(
    {"klass", "kclass", "clazz", "type1", "class1", "lambda1", "import1",
     "def1", "func1"})
MEMBER_EXEMPT: frozenset[str] = frozenset(
    {"_missing_", "_generate_next_value_", "_ignore_"})

_OPS: tuple[str, ...] = (
    "init", "new", "call", "del", "copy", "deepcopy", "getstate", "setstate",
    "reduce", "reduce_ex", "sizeof", "dir", "fspath", "get", "set", "delete",
    "set_name", "init_subclass", "class_getitem", "post_init", "prepare",
    "instancecheck", "subclasscheck", "getattr", "setattr", "delattr",
    "getattribute", "missing", "enter", "exit", "await", "aiter", "anext",
    "aenter", "aexit", "iter", "next", "reversed", "contains", "getitem",
    "setitem", "delitem", "len", "str", "repr", "bytes", "format", "hash",
    "bool", "int", "float", "complex", "index", "round", "trunc", "floor",
    "ceil", "abs", "neg", "pos", "invert", "add", "sub", "mul", "truediv",
    "floordiv", "mod", "pow", "matmul", "and", "or", "xor", "lshift",
    "rshift", "eq", "ne", "lt", "le", "gt", "ge", "divmod",
)
DUNDER_NAMES: frozenset[str] = frozenset(
    {f"__{prefix}{op}__" for op in _OPS for prefix in ("", "r", "i")}
    | {"__all__", "__doc__", "__name__", "__file__", "__module__",
       "__qualname__", "__dict__", "__weakref__", "__slots__", "__annotations__",
       "__debug__", "__build_class__", "__import__", "__match_args__",
       "__firstlineno__", "__static_attributes__"})

SUPPRESS_RE = re.compile(r"#\s*(?:naming|modularity):\s*allow\s+(\S.*?)\s*$")
ALLOW_BLANK_RE = re.compile(r"#\s*(?:naming|modularity):\s*allow\s*$")


class _Finding(NamedTuple):
    path: str
    line: int
    col: int
    rule: str
    message: str

# --- helpers ---------------------------------------------------------------

def _dotted(node: ast.expr) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def _base_names(node: ast.ClassDef) -> list[str]:
    out = []
    for base in node.bases:
        dotted = _dotted(base)
        out.append(dotted.rsplit(".", 1)[-1])
    return out


def _spelling(findings: list[_Finding], path: str, node: ast.AST, name: str,
              pattern: re.Pattern[str], expected: str, kind: str) -> None:
    if pattern.match(name):
        return
    findings.append(_Finding(path, node.lineno, node.col_offset + 1,
        "N2" if name.startswith("_") else "N1",
        f"{kind} '{name}' should be {expected}"))


def _constant_value(value: ast.expr | None) -> bool:
    """Is this the kind of value a constant is bound to (for spelling only)?"""
    if isinstance(value, ast.Constant):
        return True
    if isinstance(value, ast.Tuple):
        return all(isinstance(e, ast.Constant) for e in value.elts)
    return (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id in ("frozenset", "tuple"))


# --- checks ----------------------------------------------------------------

def _check_defs(tree: ast.Module, path: str, findings: list[_Finding]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        name = node.name
        if name in DUNDER_NAMES:
            continue
        if name.startswith("__") and name.endswith("__"):
            findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                "N3", f"'{name}' invents a dunder name; those are the "
                      "language's reserved spelling"))
            continue
        if isinstance(node, ast.ClassDef):
            _spelling(findings, path, node, name, CLASS_RE,
                      "CamelCase (_CamelCase if private)", "class")
        else:
            _spelling(findings, path, node, name, FUNC_RE,
                      "snake_case (_snake_case if private)", "function")


def _check_variables(tree: ast.Module, path: str, findings: list[_Finding]) -> None:
    module_targets: dict[tuple[int, int], ast.expr | None] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    module_targets[(target.lineno, target.col_offset)] = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            module_targets[(stmt.target.lineno, stmt.target.col_offset)] = stmt.value

    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.append(node)
        elif isinstance(node, ast.arg):
            names.append(node)
        for name_node in names:
            name = name_node.arg if isinstance(name_node, ast.arg) else name_node.id
            if name == "_" or name in DUNDER_NAMES:
                continue
            if name in KEYWORD_EVASIONS:
                findings.append(_Finding(path, name_node.lineno,
                    name_node.col_offset + 1, "N3",
                    f"'{name}' evades a keyword; take the trailing-underscore "
                    "spelling instead (class_, type_)"))
                continue
            key = (name_node.lineno, name_node.col_offset)
            if key in module_targets and not isinstance(name_node, ast.arg):
                if _constant_value(module_targets[key]):
                    _spelling(findings, path, name_node, name, CONST_RE,
                              "ALL_CAPS (_ALL_CAPS if private)", "constant")
                else:
                    _spelling(findings, path, name_node, name, NAME_RE,
                              "snake_case or ALL_CAPS", "module-level name")
            else:
                _spelling(findings, path, name_node, name, NAME_RE,
                          "snake_case or ALL_CAPS", "name")
            if name in AMBIGUOUS:
                findings.append(_Finding(path, name_node.lineno,
                    name_node.col_offset + 1, "N3",
                    f"'{name}' is not readable at a glance (l and 1, O and 0)"))



def _check_n3(tree: ast.Module, path: str, findings: list[_Finding]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, ast.Call) and _dotted(value.func).rsplit(
                    ".", 1)[-1] in _TYPEVAR_BASES:
                for target in node.targets:
                    if isinstance(target, ast.Name) and not CLASS_RE.match(target.id):
                        findings.append(_Finding(path, target.lineno,
                            target.col_offset + 1, "N3",
                            f"type variable '{target.id}' should be short "
                            "CapWords (T, AnyStr, Proto-suffixed)"))
        if isinstance(node, ast.ClassDef):
            if any(_EXCEPTION_BASE_RE.search(b) for b in _base_names(node)) \
                    and not node.name.endswith("Error"):
                findings.append(_Finding(path, node.lineno, node.col_offset + 1,
                    "N3", f"exception class '{node.name}' should end in "
                          "'Error'"))


def _check_n4(tree: ast.Module, path: str, findings: list[_Finding]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_ENUM_BASE_RE.search(b) for b in _base_names(node)):
            continue
        for stmt in node.body:
            target = None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                    and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0]
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target = stmt.target
            if target is None:
                continue
            name = target.id
            if name in MEMBER_EXEMPT or (name.startswith("__") and name.endswith("__")):
                continue
            if not CONST_RE.match(name):
                findings.append(_Finding(path, target.lineno,
                    target.col_offset + 1, "N4",
                    f"enum member '{name}' should be ALL_CAPS -- a constant "
                    "scoped to its class"))


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
        allowed = SUPPRESS_RE.search(token.string)
        if allowed:
            suppress[token.start[0]] = allowed.group(1)
        elif ALLOW_BLANK_RE.search(token.string):
            findings.append(_Finding(path, token.start[0], token.start[1] + 1,
                "SUP", "suppression without a reason; write "
                       "`# naming: allow <reason>`"))
    return suppress, findings


def _check_file(path: str) -> list[_Finding]:
    try:
        with tokenize.open(path) as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)
    except (OSError, SyntaxError) as exc:
        return [_Finding(path, 1, 1, "PARSE", f"cannot parse: {exc}")]
    suppress, findings = _read_suppressions(path)
    stem = os.path.basename(path)[:-3]
    is_dunder_stem = stem.startswith("__") and stem.endswith("__")
    if not is_dunder_stem and not MODULE_RE.match(stem):
        findings.append(_Finding(path, 1, 1, "N3",
            f"module name '{stem}' should be short all-lowercase "
            "(underscores where they improve readability)"))
    _check_defs(tree, path, findings)
    _check_variables(tree, path, findings)
    _check_n3(tree, path, findings)
    _check_n4(tree, path, findings)
    return [f for f in findings
            if f.line not in suppress and (f.line - 1) not in suppress]


def _check_packages(paths: list[str]) -> list[_Finding]:
    findings: list[_Finding] = []
    for given in paths:
        roots = [given] if os.path.isdir(given) else [os.path.dirname(given)]
        for root in roots:
            for dirpath, dirnames, _ in os.walk(root):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                if not os.path.isfile(os.path.join(dirpath, "__init__.py")):
                    continue
                name = os.path.basename(dirpath)
                pattern = PKG_PRIVATE_RE if name.startswith("_") else PKG_PUBLIC_RE
                if not pattern.match(name):
                    findings.append(_Finding(
                        os.path.join(dirpath, "__init__.py"), 1, 1, "N3",
                        f"package name '{name}' should be all-lowercase with "
                        "no underscores (private packages keep the marker "
                        "and may separate words)"))
    return findings


def _print_plan() -> None:
    print("Covered (implemented):")
    for rule_id, claim in COVERAGE:
        print(f"  {rule_id}  {claim}")
    print()
    print("Not checked (judgement or out of scope):")
    print("  -- whether a module-level name is truly a constant (B1's claim)")
    print("  -- __double_leading mangling semantics; 'undocumented is internal'")
    print("  -- the trailing-underscore keyword rule beyond the common evasions")


def main(argv: list[str] | None = None) -> int:
    """Check Python names against the python-naming rules; 1 on findings."""
    parser = argparse.ArgumentParser(
        prog="check_naming",
        description="reference checker for the python-naming skill (N1--N4)")
    parser.add_argument("paths", nargs="*", default=["."],
                        help="files or directories to check (default: current dir)")
    parser.add_argument("--plan", action="store_true",
                        help="print the coverage and exit")
    args = parser.parse_args(argv)
    if args.plan:
        _print_plan()
        return 0
    findings: list[_Finding] = []
    for given in args.paths or ["."]:
        if os.path.isfile(given):
            if given.endswith(".py"):
                findings.extend(_check_file(given))
            continue
        for dirpath, dirnames, names in os.walk(given):
            dirnames[:] = sorted(d for d in dirnames
                                 if not d.startswith(".") and d != "__pycache__")
            for name in sorted(names):
                if name.endswith(".py"):
                    findings.extend(_check_file(os.path.join(dirpath, name)))
    findings.extend(_check_packages(args.paths or ["."]))
    for finding in sorted(findings):
        print(f"{finding.path}:{finding.line}:{finding.col}: "
              f"[{finding.rule}] {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
