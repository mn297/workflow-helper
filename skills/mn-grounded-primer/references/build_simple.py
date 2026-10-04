"""Rewrite each cell lesson of code-notebook/ as a plain script in code-simple/, one comment banner per step.

A lesson mixes three things: the snippet, the check cells that assert the chapter numbers, and
notes for cell mode. The simple copy keeps the code in the same order and turns each markdown
heading into a banner, with its notes as comments below it. It drops the cell markers, the check
cells, the "Try:" lines, notes about cells, the `if "ipykernel" in sys.modules:` blocks, the last
"numbers asserted" print, and setup imports and helpers that no kept line uses. The lesson stays
the source: edit it, then run this script again. A lesson is a .py file in code-notebook/ whose
first line is "# %%".

Run from the workspace root, with <folder> the primer folder:
    .venv/bin/python <folder>/code-simple/build_simple.py          # write every simple copy
    .venv/bin/python <folder>/code-simple/build_simple.py --check  # exit 1 if a copy is stale or prints other text
--check runs each lesson and its simple copy in code-notebook/. Each copy must exit 0, and its
output lines must appear, in the same order, in the output of the lesson. A number with the unit
s or ms is a time and is ignored.
"""
import ast
import concurrent.futures
import pathlib
import re
import subprocess
import sys

SIMPLE = pathlib.Path(__file__).resolve().parent
LESSONS = SIMPLE.parent / "code-notebook"
MARKER = re.compile(r"^# %%(.*)$")
RULE = "# " + "=" * 76
HERE_LESSON = 'pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path.cwd()'
HERE_SIMPLE = 'pathlib.Path(__file__).resolve().parents[1] / "code-notebook"'  # the folder of the lesson
CELL_NOTE = re.compile(r"\bcells?\b|\bkernel\b", re.I)
DONE = re.compile(r'print\(["\']all chapter .*asserted["\']\)')
TIMES = re.compile(r"\d+(\.\d+)? m?s\b")
NUMBER = re.compile(r"\d+(\.\d+)?(e[-+]?\d+)?")
MUTATORS = {"append", "extend", "insert", "pop", "remove", "clear", "update", "add", "discard", "setdefault",
            "sort", "reverse", "fill"}
NOTE = ("Simple copy of code-notebook/{name}: the same code in the same order, without check\n"
        "cells and cell markers. build_simple.py writes this file. Edit the lesson, not this file.")


def lessons():
    return sorted(p for p in LESSONS.glob("*.py") if p.read_text().startswith("# %%\n"))


def split_cells(text):
    """Split a lesson into (kind, lines) with kind "markdown", "check" or "code"."""
    cells = []
    for line in text.splitlines():
        m = MARKER.match(line)
        if m:
            title = m.group(1).strip()
            kind = "markdown" if title.startswith("[markdown]") else "check" if title.startswith("check") else "code"
            cells.append((kind, []))
        else:
            cells[-1][1].append(line)
    return cells


def banner(lines):
    """Turn a markdown cell into a banner: the heading in a box, then the notes as comments."""
    text = [re.sub(r"^#( |$)", "", line) for line in lines]
    heading = next((t.lstrip("#").strip() for t in text if t.startswith("#")), None)
    notes = [t for t in text if t.strip() and not t.startswith("#")
             and not t.startswith("Try:") and not CELL_NOTE.search(t)]
    out = [RULE, "# " + heading, RULE] if heading else []
    return out + ["# " + t for t in notes]


def strip_cell(code):
    """Drop top-level ipykernel blocks and full-line comments about cells or the kernel."""
    tree = ast.parse(code)
    drop = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.If) and "ipykernel" in ast.unparse(stmt.test):
            drop.update(range(stmt.lineno, stmt.end_lineno + 1))
    lines = [line.replace(HERE_LESSON, HERE_SIMPLE) for n, line in enumerate(code.splitlines(), start=1)
             if n not in drop and not (line.lstrip().startswith("#") and CELL_NOTE.search(line))]
    return "\n".join(lines).strip("\n")


def names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def reads(stmt):
    """Names a top-level statement reads from earlier statements.

    Loop and comprehension variables, function arguments and names assigned inside a function do not
    count. The rule is rough: a name that is both such a local and a read elsewhere in the same
    statement is missed, and --check then fails.
    """
    local = set()
    for node in ast.walk(stmt):
        if isinstance(node, (ast.For, ast.comprehension)):
            local |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        elif isinstance(node, (ast.FunctionDef, ast.Lambda)):
            args = node.args
            local |= {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs + [args.vararg, args.kwarg] if a}
            if isinstance(node, ast.FunctionDef):
                local |= {n.id for s in node.body for n in ast.walk(s) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    out = {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Store)}
    out |= {n.target.id for n in ast.walk(stmt) if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name)}
    out |= {f"{n.value.id}.{n.attr}" for n in ast.walk(stmt) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    return out - local


def binds(stmt, modules=frozenset()):
    """Names a top-level statement binds or changes in the module scope. Comprehension and function locals do not count.

    Setting an attribute of a module, as in sys.stdout = ..., changes only that attribute.
    """
    if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
        return {stmt.name}
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return {(a.asname or a.name).split(".")[0] for a in stmt.names}
    out, todo = set(), [stmt]
    while todo:
        node = todo.pop()
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            out.add(node.id)
        elif (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name)
              and node.value.id in modules):
            out.add(f"{node.value.id}.{node.attr}")
        elif isinstance(node, (ast.Subscript, ast.Attribute)) and isinstance(node.ctx, ast.Store):
            out |= {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}  # x[0] = ... changes x
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in MUTATORS
              and isinstance(node.func.value, ast.Name)):
            out.add(node.func.value.id)  # rows.append(...) changes rows
        if not isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Lambda,
                                 ast.FunctionDef, ast.ClassDef)) or node is stmt:
            todo.extend(ast.iter_child_nodes(node))
    return out


def overwrites(stmt):
    """Names that a top-level statement always replaces, so an earlier value is dead.

    A for loop counts: the lessons loop over sequences that are never empty.
    """
    if isinstance(stmt, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
        return binds(stmt)
    targets = (stmt.targets if isinstance(stmt, ast.Assign)
               else [stmt.target] if isinstance(stmt, (ast.AnnAssign, ast.For)) else [])
    return {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


def keep_needed(blocks, modules):
    """Replace each check cell by its statements that bind a name a later kept line reads.

    A check cell sometimes computes a value that a later step uses. Walk the statements backward
    with the set of names still to be read, and keep such a statement with what it reads in turn.
    """
    needed = set()
    for _, cells in reversed(blocks):
        for i in reversed(range(len(cells))):
            kind, code = cells[i]
            lines, kept = code.splitlines(), []
            for stmt in reversed(ast.parse(code).body):
                if kind == "check" and not binds(stmt, modules) & needed:
                    continue
                if kind == "check":
                    kept.insert(0, "\n".join(lines[stmt.lineno - 1:stmt.end_lineno]))
                needed = (needed - overwrites(stmt)) | reads(stmt)
            if kind == "check":
                cells[i] = ("code", "\n".join(kept))


def prune_setup(setup, rest, lesson_name):
    """Cut the docstring to its first paragraph and a note, and drop setup imports and helpers that no kept line uses."""
    tree = ast.parse(setup)
    used = names(ast.parse(rest))
    defs = [s for s in tree.body if isinstance(s, (ast.FunctionDef, ast.ClassDef))]
    imports = [s for s in tree.body if isinstance(s, (ast.Import, ast.ImportFrom))]
    for s in tree.body:
        if s not in defs and s not in imports:
            used |= names(s)
    kept, grew = set(), True
    while grew:  # a kept helper can use another helper
        grew = False
        for s in defs:
            if s.name in used and s.name not in kept:
                kept.add(s.name)
                used |= names(s)
                grew = True
    lines = setup.splitlines()
    replace = {}  # first line -> (last line, new text or None to drop)
    for s in defs:
        if s.name not in kept:
            replace[min([s.lineno] + [d.lineno for d in s.decorator_list])] = (s.end_lineno, None)
    for s in imports:
        if getattr(s, "module", None) == "__future__" or "noqa" in lines[s.end_lineno - 1]:
            continue  # a side-effect import carries a noqa comment
        alive = [a for a in s.names if a.name == "*" or (a.asname or a.name).split(".")[0] in used]
        if len(alive) != len(s.names):
            s.names = alive
            replace[s.lineno] = (s.end_lineno, ast.unparse(s) if alive else None)
    doc = tree.body[0]
    if isinstance(doc, ast.Expr) and isinstance(doc.value, ast.Constant) and isinstance(doc.value.value, str):
        raw = "\n".join(lines[doc.lineno - 1:doc.end_lineno])  # source text, so escapes stay as written
        opening = re.match(r"[rRuU]?(\"\"\"|''')", raw).group(0)
        summary = raw[len(opening):-3].strip().split("\n\n")[0]
        summary = "\n".join(line for line in summary.splitlines() if not line.startswith("Must print"))
        replace[doc.lineno] = (doc.end_lineno, f"{opening}{summary}\n\n{NOTE.format(name=lesson_name)}\n{opening[-3:]}")
    doc_end = doc.end_lineno if doc.lineno in replace else 0
    out, n = [], 1
    while n <= len(lines):
        if n in replace:
            first, (last, text) = n, replace[n]
            n = last + 1
            if text is not None:
                out.append(text)
            elif first == doc_end + 1 or out and not out[-1].strip():
                while n <= len(lines) and not lines[n - 1].strip():  # leave no gap where the line was
                    n += 1
        else:
            out.append(lines[n - 1])
            n += 1
    return re.sub(r"\n{3,}", "\n\n\n", "\n".join(out)).strip("\n")


def simplify(path):
    """Return the simple copy of one lesson as text."""
    blocks = [([], [])]  # (banner lines, [(kind, code)])
    for kind, lines in split_cells(path.read_text()):
        if kind == "markdown":
            blocks.append((banner(lines), []))
        else:
            code = strip_cell("\n".join(lines))
            if code and not DONE.fullmatch(code):
                blocks[-1][1].append((kind, code))
    modules = {name for _, cells in blocks for _, code in cells for s in ast.parse(code).body
               if isinstance(s, ast.Import) for name in binds(s)}
    keep_needed(blocks, modules)
    blocks = [(head, [code for _, code in cells if code]) for head, cells in blocks]
    setup, *first_rest = blocks[0][1]
    blocks[0] = ([], first_rest)
    blocks = [b for b in blocks if b[1]]
    rest = "\n\n".join(c for _, cells in blocks for c in cells)
    if "__file__" in (setup + rest).replace(HERE_SIMPLE, ""):
        sys.exit(f"{path.name}: uses __file__ outside the HERE line of interactive-exercises.md")
    parts = [prune_setup(setup, rest, path.name)]
    for head, cells in blocks:
        parts.append("\n".join(head + [""] + ["\n\n".join(cells)]) if head else "\n\n".join(cells))
    return "\n\n\n".join(parts) + "\n"


def output_lines(path):
    run = subprocess.run([sys.executable, str(path)], cwd=LESSONS, capture_output=True, text=True, timeout=1800)
    return run.returncode, [TIMES.sub("<t> s", line) for line in run.stdout.splitlines()], run.stderr


def test(lesson):
    """Run a lesson and its simple copy. Return a problem, or None."""
    code, want, _ = output_lines(lesson)
    if code:
        return f"the lesson exits {code}"
    code, got, err = output_lines(SIMPLE / lesson.name)
    if code:
        return f"the simple copy exits {code}: {err.strip().splitlines()[-1] if err.strip() else ''}"
    lines = iter(want)
    missing = next((line for line in got if not any(line == w for w in lines)), None)
    if missing is not None:
        hint = ""
        if NUMBER.sub("#", missing) in {NUMBER.sub("#", w) for w in want}:
            hint = " (only numbers differ: if one is a time, print it with its unit, as 12.3 ms)"
        return f"the simple copy prints a line that the lesson does not print in this order: {missing!r}{hint}"
    return None


def main():
    check = "--check" in sys.argv[1:]
    sources = lessons()
    copies = {p.name: simplify(p) for p in sources}
    orphans = sorted(p.name for p in SIMPLE.glob("*.py") if p.name != "build_simple.py" and p.name not in copies)
    if not check:
        for name, text in copies.items():
            (SIMPLE / name).write_text(text)
        for name in orphans:
            (SIMPLE / name).unlink()
        print(f"wrote {len(copies)} simple copies to {SIMPLE.relative_to(SIMPLE.parent.parent)}/"
              + (f", removed {', '.join(orphans)}" if orphans else ""))
        return
    stale = [n for n, t in copies.items() if not (SIMPLE / n).exists() or (SIMPLE / n).read_text() != t] + orphans
    if stale:
        print(f"stale simple copies: {', '.join(stale)}. Run code-simple/build_simple.py.")
        sys.exit(1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        problems = list(pool.map(test, sources))
    for lesson, problem in zip(sources, problems):
        print(f"{'FAIL' if problem else 'OK  '}  code-simple/{lesson.name}" + (f": {problem}" if problem else ""))
    failed = sum(p is not None for p in problems)
    print(f"{failed} of {len(sources)} simple copies failed" if failed else f"all {len(sources)} simple copies match their lessons")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
