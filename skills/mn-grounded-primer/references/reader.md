# Course reader (wave 5, after the visualizer)

One generated page, `<folder>/index.html`, lets the reader go through the
primer in a browser instead of raw markdown. Reference instance:
`/home/john/force_location/tutorial-particle-filter/index.html`, built
2026-10-03, with 16 pages and 2,616 formulas.

## What it shows

- Landing page: the primer title and the first README paragraph. Buttons
  for "Start with chapter 01" (or "Continue" with the last chapter read),
  "Open the instruments" and "Course plan". One card per chapter with the
  question and the hours from the README chapter table. Cards for the
  course plan, the notebook code and the resources.
- Lesson view: a left panel with Home, the chapters, the course pages and the
  instruments. The rendered chapter with its math. An "On this page" list
  on wide screens. Previous and next buttons. A button that opens the
  chapter's station, `viz/<name>.html#sNN`.
- Code view: a "Simple code" page lists each simple copy of
  `code-simple/` under its chapter. A chapter page has one "Simple code"
  button per copy. The code view shows the copy with Python colors,
  one block per step, and a "Steps" list on wide screens. It links back to
  the chapter and to the notebook version in `code-notebook/`.
- Links: a markdown link to another primer `.md` file opens that page in
  the reader. Inline code that names an existing file or folder, with or
  without `:line`, becomes a link to it. External links open in a new tab.

## Steps

1. Copy `references/build_reader.py` to `<folder>/viz/build_reader.py`. If
   the folder follows section 2 of `SKILL.md`, the script needs no edits:
   - chapter files `NN-<slug>.md`,
   - README chapter table rows of the form ``| NN | `NN-<slug>.md` | question | time |``,
   - `code-notebook/README.md`, `resources.md` and one page in `viz/`,
   - the simple copies in `code-simple/` (`interactive-exercises.md`,
     section "Simple copies"). Without them the reader has no code view.
2. Run `.venv/bin/python <folder>/viz/build_reader.py` from the workspace
   root. Completion: it writes `index.html`, and `--check` exits 0.
3. Link the visualizer back to the reader. Put an "All lessons" link to
   `../index.html` in its header. On each station, put a "Read chapter NN"
   link to `../index.html#cNN`. Set it in the function that switches
   stations. Run the node check again. Completion: it still passes.
4. Render in the same isolated headless Chrome as the visualizer. On every
   page, count the `[data-tex]` elements and those with an `mjx-container`
   inside. The two counts must be equal, with no `mjx-merror`. No paragraph
   can show a stray `$`. The chapter button must open `#sNN`, and the station link must
   return to `#cNN`. Each code view must show one `pre.phase` per step and
   the `.hljs-keyword` spans of highlight.js. A 390 px viewport in dark mode must not scroll
   sideways. Completion: every page passes.
5. Copy `references/run.sh` to `<folder>/run.sh` and make it executable.
   It writes the simple copies again, rebuilds `index.html` and serves it on
   `127.0.0.1`. Completion: the
   reader URL it prints returns 200. A `.py` link returns
   `text/plain; charset=utf-8`. A second start on the same port exits 1
   with a message.
6. In the primer README, next to the visualizer, say what `index.html` is
   and that `run.sh` serves it. Say that it loads marked and MathJax from
   cdnjs. Say that `run.sh` or `build_reader.py` must run again after any
   markdown edit. The published Artifact copy of
   the visualizer has no reader next to it. Publish before step 3, or say in
   the README that the published copy has no reader links.

## Mechanics that worked

- Embed the markdown as JSON in a `<script type="application/json">` tag,
  with `</` escaped. A `fetch` of a local file fails under `file://`, and
  the reader must open from disk.
- Hide the math from marked. Split out fenced code line by line. Replace
  inline code spans with placeholders, then `$$...$$` and `$...$` with
  private-use characters (U+E000). Restore the code spans, run marked, and
  turn the placeholders into spans with a `data-tex` attribute. Otherwise
  marked eats `_` and `*` inside TeX and splits table rows on `|`.
- Render each span with `MathJax.tex2svg(tex, {display})` after
  `MathJax.startup.promise`. Use `fontCache: "local"` and add
  `MathJax.svgStylesheet()` once. Outside a document typeset, the global
  font cache leaves glyphs undefined.
- Build the "On this page" list from heading `innerHTML` before you
  typeset, so headings with math render in the list too.
- marked 18 on cdnjs has no root `marked.min.js`. Use
  `lib/marked.umd.min.js`.
- highlight.js 11 from cdnjs colors the code view. Its theme CSS is not
  loaded. The template colors the `.hljs-*` classes with its own light and
  dark tokens. Without the CDN, the code shows in one color.
- A file name has no spaces, so it does not wrap. A pager button or a card
  with a file name overflowed the 390 px viewport. These elements need
  `overflow-wrap:anywhere`.
- Give `pre` its own font size and line height. A `code` element inside a
  `pre` with the body line height kept the 25.6 px lines of 16 px text.
- Serve the primer with `run.sh`, not from disk. Chrome stores the zoom of
  a `file://` page under its full URL, with the hash, so each lesson kept
  its own zoom. Over `http://127.0.0.1`, Chrome stores zoom per host, and
  every lesson and the visualizer share one level. A CSS zoom script did
  not fix it: Chrome's own per-URL zoom still applied on top.
- `run.sh` serves the parent of the primer folder, so the `../` code links
  resolve. It adds `charset=utf-8` to text types and serves `.py` and `.md`
  as `text/plain`. Without the charset, Chrome showed `§` as `Â§`. Its port
  probe sets `SO_REUSEADDR`, like the server. Without it, a restart within
  a minute reported the port as busy.
