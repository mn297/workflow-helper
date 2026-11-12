# The rewrite page

One HTML page per paper. Start from `assets/page.html`: copy it, then fill
it. A `⟦...⟧` in the template is a slot to fill; the lint fails while one is
left. Keep its styles and its section order. Every paper gets the same page
shape, so I learn where each thing sits; a new design per paper would cost me
that.

## Where it goes

- In a project: follow mn-organizing-project-docs, with the topic folder
  `papers`. The page is `docs/papers/<slug>.html`, and the derivation checks
  are `docs/papers/<slug>.checks.py`. Add the card to `docs/index.html`.
- With no project: next to the paper's source, as `rewrite.html` and
  `checks.py`.
- Publish the same file with the Artifact tool when the session has it, and
  give me the link.

## Sections, in order

The lint checks these ids and their order. The last column maps each section
to the rung of `references/trace.md` it answers.

| id | It holds | Rung |
|---|---|---|
| `breath` | the arrow chain, the purpose, the few words the chain needs, what is new and what is borrowed | 1 |
| `system` | the system diagram, the method as one box, what is unknown, when it runs | 2, 3, 4, 5, 8 |
| `example` | the running example's numbers, each with its place in the paper, or a mine mark when the data or your own run gives it | all |
| `stages` | one `section.stage` per stage, in the order the data flows | 4, 5 |
| `objective` | each term of the objective, and how one unknown reaches it | 6, 7 |
| `evidence` | one row per claim, quoted: evidence, against what, my read | 9 |
| `gaps` | what is unsaid, where paper and code disagree, what can fake the result | 9 |
| `rebuild` | the build order with a check per step, and every knob with its value | |
| `ours` | optional: how it maps onto my project | 10 |
| `restate` | a "so basically" paraphrase, and the common wrong readings | |
| `ledger` | every quantity: name, symbol, kind, shape, unit, source | 3 |
| `coverage` | every numbered item of the paper, placed where its content is, or skipped with a reason | |
| `open` | what the source did not settle; what else was read; the unchecked count | |

A section that does not apply keeps its heading and says so in one line. The
reference tables sit last because I look things up in them; I do not read
them top to bottom.

## A stage chapter

Each chapter opens with the takeaway and the contract. The other parts follow
in the order below, unless the reader needs one earlier: a prerequisite
before the paragraph that uses it, a glue fact at the step that needs it.
Drop a part only when the stage has none.

1. **Takeaway.** One bold sentence.
2. **Contract.** The table of what the stage reads, its knobs, and what it
   makes: name, symbol, kind, shape, unit or frame, and where each comes from
   or goes to. Shapes use the running example's counts beside the letters:
   `(N, 3)`, N = 1,630.
3. **Mechanism in words.** What changes, and what makes it change. Give a
   physical picture. Two to four sentences per paragraph.
4. **Figure**, when geometry or the layout of data matters. See Figures.
5. **Prerequisite**, just before its first use: a concept the paper assumes
   (a Lie group, the ELBO, a FiLM layer) in three to five lines, with only
   what this stage uses, and a pointer to a fuller source. A glossary at the
   top would make me read ten definitions before the first idea. The one
   exception is the one-breath chain: the words it uses, five at most, get
   their plain meaning in one line under it.
6. **Mechanism in code.** Five to twenty lines, the shape of each array in a
   comment. Take it from the official code when there is one, with
   `file:line`; write it yourself otherwise and mark it `mine`.
7. **The math.** Each equation in a box, its legend right under it, then its
   derivation. See the rules in `SKILL.md`.
8. **On the running example.** The numbers going in and coming out.
9. **Without this stage.** What breaks, with the paper's ablation when it has
   one. When it has none, say that the paper does not test it.
10. **Glue facts**, at the place each is first needed.

## Markup that the lint reads

`scripts/check_page.py` tests structure through these classes and attributes.

- **Contract:** `<table class="contract">` inside its `section.stage`. Each
  row carries `data-io` (`in`, `param`, `state` or `out`) and `data-q`, a
  short id of the quantity that is the same on every row that names it.
  `state` is a quantity the stage keeps from its own last iteration.
- **Ledger:** `<table class="ledger">`, one row per quantity, with `data-q`
  and `data-kind` (one of the seven kinds). The accounting check joins the
  contracts to the ledger through `data-q`.
- **Equation:** `<div class="eq" id="eq-7">`, and its `<dl class="vars">` as
  the very next element. A legend row gives the symbol in `\(...\)`, then the
  meaning, the unit, the shape and where the value comes from. Raw Greek or
  math characters in a legend's `dt` get a warning: they do not render as
  math.
- **Derivation step:** `<div class="eq s">` inside
  `<details class="deriv"><ol class="steps">`. A step needs no legend; it
  uses the symbols of the box above it. Add the `open` attribute to the
  `details` of the derivation the method hinges on.
- **Marks:** `<span class="src p">Sec. 3.2, Eq. 7</span>`,
  `<span class="src c">model.py:120</span>`,
  `<span class="src m ok">mine, checked: checks.py::jacobian</span>`,
  `<span class="src m">mine, unchecked</span>`. The lint warns about a
  derivation step, a glue fact, or a row of the example, evidence and knob
  tables that has no mark. It fails when a mark names a function that the
  checks file next to the page does not have.
- **Kinds:** `<span class="k learned">learned</span>`. Always print the word.
  In a diagram, colour a quantity's name with the class `q-learned`.
- **Coverage:** `<table class="coverage">`. A row holds a link to the id that
  covers the item, or a `<td class="skip">` with the reason. Link a results
  table to the row that quotes its numbers. When the page uses only part of
  an item, the row says which part it leaves out: I read "placed" as "I need
  not open the paper for this".

## Figures

- The system diagram is required. It has three lanes: once (preprocessing),
  loop (the training or solve loop) and use (what runs on new data). One box
  per stage. Every arrow carries the name and the shape of what flows on it,
  coloured by its kind.
- A stage figure shows the mechanism: what moves, what is compared with what,
  where a quantity lives. A box with the stage's name in it shows nothing.
- Draw your own figure as inline SVG; load artifact-diagramming first. Refer
  to the paper's figures by number. Do not paste them in: most are result
  figures, and they belong to the publisher.
- A drawing that uses made-up numbers says so in its caption.

## An interactive toy

Add one where moving a knob is the insight: a kernel's scale, a step size, a
window length. At most three per page. Each toy is small enough to hold in
the head (one joint, sixteen points), runs the paper's actual rule, and
labels its numbers as toy numbers. It opens in a state that already shows
the point, so the page says something before I touch it. Three traps:

- A class that sets `display` overrides the `hidden` attribute. The template
  has `[hidden] { display: none !important; }` for that.
- MathJax measures nothing inside `display: none`. To switch a panel that
  holds math, move it off-screen (`position: absolute; left: -10000px;
  visibility: hidden`) and do not hide it.
- In a monospace label, θ reads as 0 and l as 1. Write the word.

## Writing

- Open every section with one bold sentence that is its takeaway.
- One idea per paragraph, two to four sentences, lines no wider than 68
  characters.
- Keep the paper's term so I can search for it, and give its plain meaning
  in the same line at first use.
- One name per thing. When the paper uses two names for one thing, or one
  symbol for two, say so once and pick one.
- Every number has its unit and its place in the source.
- Use a table for any side-by-side comparison, and say in one sentence how
  to read it.

## The checks file

One Python file, numpy and the standard library only. One function per
checked step, named in the page's mark. Each function builds a small random
instance, asserts the identity or compares a gradient with a finite
difference, and prints one line. `python <file>` runs them all.

A check that needs more (the released data, a GPU, another package) lives in
the same file and prints "skipped" with the reason when its input is absent.
A check that exists only in your scratch folder is gone when I read the page.
The run behind the running example is a check too: it prints the numbers the
page quotes, and its docstring lists the settings you chose.

## The cold-read brief

Give the fresh subagent the page, the source folder, and this text:

> Read the page as a newcomer to the paper. Then check it against the
> source. Return five lists. Give each item the page's section id and the
> place in the source. (1) Statements that contradict the source, or that
> contradict the page itself: test the lede and each bold takeaway against
> the text under it. (2) Numbers that are not in the source. (3) Marks that
> claim more than they cover: a paper mark on a reason, a cause or a
> protocol that the paper does not write at that place; a "checked" mark
> whose check would still pass if the statement were false; a claim in the
> evidence table that is stronger than the paper's sentence. (4) Symbols or
> terms used before the page defines them. (5) Steps you could not follow,
> with the line where you got lost. Do not rewrite the page.

Fix what the lists show. A list item you disagree with goes to the open
questions with both readings.

## Before you publish

1. `python scripts/check_page.py PAGE.html` prints no error, and each
   warning is fixed or explained in the report.
2. `python <slug>.checks.py` passes.
3. `python scripts/render_check.py PAGE.html` prints no error. It needs
   Chrome or Chromium. It tests a desktop and a phone width for MathJax
   errors, a page that scrolls sideways, and clipped or overlapping diagram
   labels, and it saves a screenshot of the top and of each figure. Open
   those: a script cannot tell whether a drawing explains anything.
