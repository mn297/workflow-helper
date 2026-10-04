# Interactive exercise scripts

Every exercise script is a plain `.py` file with two modes. In script mode,
`python exNN_<slug>.py` runs top to bottom, asserts the chapter numbers and
exits 0. In cell mode, an editor runs it one cell at a time in a Jupyter
kernel. Lines that start with `# %%` mark the cells. VS Code (Run Cell,
Interactive Window), Spyder, PyCharm and Jupytext read these markers. Both
modes print the same numbers. The reader never gets a `.ipynb` file.

Instance: `/home/john/practice_kinematics/tutorial-lie-algebra/exercises/`.
`ex03_exp_log_so3.py` is the model file. Read it before writing the first
script of a new primer.

## Markers

- A code cell starts with `# %%`. A check cell starts with `# %% check`.
- A markdown cell starts with `# %% [markdown]`. Every line below it starts
  with `# `, or is a bare `#` for a blank line.
- Line 1 is `# %%`. The module docstring stays the first statement, inside
  that first cell.

## Order of cells

1. Setup cell: the docstring (chapter, section, numbers it must print), the
   imports, and the `check` helper.
2. Title cell (markdown): `# Chapter NN. <title>`, then three to five lines.
   They name the snippet and the chapter section to keep open. They state the
   check-cell rule: "If you change an input to experiment, that check fails.
   Run the cell above it again with the original value."
3. One block per step of the snippet:
   - markdown cell: `## Step k. <what the step shows>`, one to four lines on
     what the code computes, what to expect, and the chapter section. Where
     the step has an input to change, one `Try:` line names a concrete change
     and its effect.
   - code cell: the snippet lines of that step, which compute and print.
   - check cell: the asserts on the numbers of that step.
4. Helpers (hat, Exp, Log, ...) get their own step. The markdown cell names
   each helper in one line.
5. Chapter exercises (section 7): one block per exercise with a computable
   answer. Markdown: `## Exercise N (chapter NN, section 7)`, the question,
   and "Work it on paper first.". Code: compute and print the answer. Check:
   assert the answer of the chapter. An exercise without a computable answer
   gets a markdown cell that points at the step that answers it.
6. Anchor and library checks: a markdown cell `## Anchor check: <claim>` or
   `## Library check: <claim>` states the claim in one or two lines. The code
   cell below it imports what it needs and holds the asserts and a print.
7. Extra checks: a number that the chapter measures outside the snippet (a
   second seed, a variant, a finite-difference test) gets a markdown cell
   `## Extra check: <claim>` and a check cell that computes and asserts it.
8. Command-line flags go into a settings cell near the top (see Hard rules).
   A long drawing helper (a GIF writer) stays one function in its own cell.
   The flow that calls it goes into cells.
9. Last cell: `print("all chapter NN numbers asserted")`.

## Hard rules

- Snippet lines stay verbatim from chapter section 6. They are split across
  cells, not edited. A reader who compares the chapter with the script finds
  the same lines, in the same order. You can add a line between them only to
  make a cell safe to run twice. Example from a filter: the predict cell
  ends with `Rh_minus = Rh`, and the update cell starts with `Rh = Rh_minus`.
- Every cell can run twice in a row with the same result. Do not change a
  name from an earlier cell in place. Examples: `x += 1`, `lst.append`,
  `arr[0] = ...` on a global of another cell.
- A loop that accumulates starts from its initial value inside the same
  cell. Filter steps, Gauss-Newton iterations and integrators are loops of
  this kind. Another way: give each step new names (`x1`, `x2`). Build and
  solve a gtsam graph or `Values` object in one cell.
- A random generator (`np.random.default_rng(seed)`) is created inside the
  cell that draws from it, so a rerun draws the same numbers.
- Output goes through `print`. A bare expression prints nothing in script
  mode.
- No `__file__` without a fallback, because a Jupyter kernel has none. The
  editor starts the kernel in the folder of the file, so use:

  ```python
  HERE = pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path.cwd()
  ```
- No `def main()` with `if __name__ == "__main__":` around the flow. In a
  kernel, `sys.argv` holds kernel arguments, not script flags. A flag stays a
  `"--flag" in sys.argv[1:]` test on its own line, with a comment that tells
  the reader to set the constant by hand.
- Matplotlib scripts use the Agg backend and write their files. After a GIF
  is written, show it in cell mode:

  ```python
  if "ipykernel" in sys.modules:  # cell by cell in a Jupyter kernel: show the GIF inline
      from IPython.display import Image as GifImage, display
      display(GifImage(filename=str(path)))
  ```
- The workspace environment needs `ipykernel`. If it is missing, add it in
  wave 0.

## Prose in markdown cells

Simple English: sentences under 25 words, active voice, no contractions, no
em-dashes, no semicolons. Plain words and code names for math (`Exp(a)
Exp(b)`, `R^T R`, `pi/2`). Use `$...$` only for a short formula that plain
text cannot carry. Do not restate the chapter. Say what the cell does and
point at the section.

## The cell-mode test

Copy `references/run_cells.py` into `exercises/` unchanged. It runs each code
cell twice in a fresh Jupyter kernel that starts in `exercises/`. The second
run must succeed and print the same text as the first, except times in
seconds. The kernel
has no `__file__` and has kernel arguments in `sys.argv`, as in the VS Code
Interactive Window. It fails a script that needs `__file__` or a flag, and a script without
cells. A cell that changes a name from an earlier cell fails in one of two
ways: the rerun prints other numbers, or a later check fails. One case stays
hidden: a cell that breaks only after the reader goes back and runs an
earlier cell again.
`run_all.sh --cells` runs it after the script mode.

Two more checks, run from the primer folder once all scripts exist. First,
every non-blank line of the section 6 block of each chapter appears in its
script, in order:

```python
import pathlib, re
for script in sorted(pathlib.Path("exercises").glob("ex[0-9][0-9]_*.py")):
    chapter = next(pathlib.Path(".").glob(f"{script.name[2:4]}-*.md")).read_text()
    block = re.search(r"^## 6\..*?```python\n(.*?)```", chapter, flags=re.S | re.M).group(1)
    lines = iter(l.rstrip() for l in script.read_text().splitlines())
    missing = [l for l in block.splitlines() if l.strip() and not any(l.rstrip() == x for x in lines)]
    print("OK " if not missing else "BAD", script.name, missing[:2])
```

Second, for an older script that you convert, count its `check(`,
`printed(` and `assert` calls before and after. The count must not fall, and the old
stdout must appear, line for line and in order, inside the new stdout.

A kernel adds its working folder to `sys.path`. If that folder holds a
directory with the name of an installed package, the import picks the
directory. In the Lie primer, a kernel started in the workspace root found
the Drake submodule `./drake/`, and `import pydrake.multibody.plant` failed
with `ImportError: initialization failed`. The exercises README tells the
reader to keep the kernel in the folder of the script.

## Exercises README

Add a section "Run a lesson cell by cell" to `exercises/README.md`. It
names the three cell kinds and the check-cell rule. It gives the VS Code
steps: select the interpreter, press Shift+Enter, run from the top. It tells
the reader to keep the kernel in the folder of the script and to start the
editor from a shell without ROS. It ends with the two test commands.
