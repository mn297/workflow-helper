# Chapter template

File name: `NN-<slug>.md`. Length 1,500 to 3,500 words. Headings exactly as
below, numbered, so the verifier can find each section by name.

```
# NN. <Title as a plain noun phrase>

## 1. Why this matters here
Two or three sentences. Tie the concept to the anchor and to the alternative
the reader keeps hearing about (the other engine, the other library).

## 2. Concepts from scratch
Define every term at first use, in one sentence each, before any equation
uses it. Build only on earlier chapters. No forward references except
"chapter NN defines X" where chapter NN really does.

## 3. Pen-and-paper derivation
One derivation, every step shown. Then a tiny worked example with real
numbers (a 1-DOF system, a 2-link chain, a 3-body tree). The reader must be
able to redo it on one sheet of paper.

## 4. In our code
Where the formula lives: `../<dir>/file.py:line-line` or
`upstream/<lib>/file:line`, a path that starts at the primer folder, verified
by reading the file in this session, not from memory. Quote the anchor's own measured
numbers with their conditions (model, thread count, step size) and the
document they come from.

## 5. In other tools
How the alternatives do the same thing (engines, libraries, papers). Facts
with sources. Mark an inference as an inference.

## 6. Snippet
One fenced numpy block under 50 lines. It prints the worked-example numbers
from section 3 and nothing else. Write it as short steps, one blank line
apart, each step printing its own numbers. The verifier splits it, line for
line, into the cells of the interactive lesson `code-notebook/exNN_<slug>.py`,
so it must run standalone.

## 7. Exercises
Three. Each with its answer directly below it, worked, not only the result.

## 8. Further reading
Names only: book, paper, lecture series. No URLs. `resources.md` holds the
verified links.
```

Length guidance per section: 1 is short, 2 and 3 carry half the chapter, 4
and 5 a quarter, 6 to 8 the rest.
