"""Run each exercise script cell by cell in a Jupyter kernel, the way an editor runs it.

A cell starts at a line that begins with "# %%". Markdown cells ("# %% [markdown]") are
skipped. Each code cell runs twice in a row, and the second run must succeed and print the
same text as the first, except times in seconds. So a cell that changes a name from an earlier
cell fails here. The kernel starts in this folder, has no __file__ and has kernel arguments
in sys.argv, as in the VS Code Interactive Window. Exit status 0 if every script passes, 1 if
one or more fail.

Run from the workspace root:
    .venv/bin/python tutorial-lie-algebra/exercises/run_cells.py              # every script
    .venv/bin/python tutorial-lie-algebra/exercises/run_cells.py ex03_exp_log_so3.py    # one script
"""
import pathlib
import re
import sys

from jupyter_client.manager import start_new_kernel

HERE = pathlib.Path(__file__).resolve().parent
MARKER = re.compile(r"^# %%(.*)$")
SECONDS = re.compile(r"\d+(\.\d+)? s\b")


def cells(path):
    """Split a script into (first line number, title, code) for each code cell."""
    out, title, start, lines = [], None, 1, []
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        m = MARKER.match(line)
        if m:
            if lines and title is not None and "[markdown]" not in title:
                out.append((start, title.strip(), "\n".join(lines)))
            title, start, lines = m.group(1), n, []
        else:
            lines.append(line)
    if lines and title is not None and "[markdown]" not in title:
        out.append((start, title.strip(), "\n".join(lines)))
    return out


def run(path):
    code_cells = cells(path)
    if not code_cells:
        return f"no '# %%' cells in {path.name}"
    km, kc = start_new_kernel(kernel_name="python3", cwd=str(HERE))
    try:
        for line, title, code in code_cells:
            printed = []
            for attempt in ("first run", "second run"):
                errors, text = [], []

                def hook(msg):
                    if msg["msg_type"] == "error":
                        errors.append(f"{msg['content']['ename']}: {msg['content']['evalue']}")
                    elif msg["msg_type"] == "stream":
                        text.append(msg["content"]["text"])

                reply = kc.execute_interactive(code, timeout=600, output_hook=hook)
                where = f"cell at line {line} ({title or 'untitled'}), {attempt}"
                if reply["content"]["status"] != "ok":
                    err = errors[0] if errors else reply["content"].get("ename", "error")
                    return f"{where}: {err}"
                printed.append(SECONDS.sub("<t> s", "".join(text)))
            if printed[0] != printed[1]:
                return f"{where}: prints other text than the first run"
        return None
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)


def main():
    names = sys.argv[1:] or sorted(p.name for p in HERE.glob("*.py") if p.name != "run_cells.py")
    failed = 0
    for name in names:
        path = pathlib.Path(name)
        if not path.is_file():
            path = HERE / path.name
        problem = run(path)
        if problem:
            failed += 1
            print(f"FAIL  {path.name}: {problem}")
        else:
            print(f"PASS  {path.name} ({len(cells(path))} code cells)")
    if failed:
        print(f"{failed} script(s) failed in cell mode")
        sys.exit(1)
    print("all scripts passed in cell mode")


if __name__ == "__main__":
    main()
