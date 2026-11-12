# pstack + ponytail: what I use and how

As of 2026-11-05. pstack 0.15.36 (`pstack@cursor-plugins`), ponytail 5.3.3 (`ponytail@ponytail`).
Read from the installed files under `~/.claude/plugins/cache/`, plus poteto's guide in
`~/.claude/plugins/cache/cursor-plugins/pstack/0.15.36/docs/guide/`.

**The short version.** ponytail is always on and makes every agent write the smallest complete change.
pstack does nothing until I type `/pstack:<name>`. My daily loop: work on main, `/ponytail-review`
before a commit, `/pstack:interrogate` when a missed bug costs a lot, `/ponytail-audit <folder>`
before a cleanup, `/pstack:benchmark-checklist` before I report a number.

---

## 1. Setup now

| Plugin | State | How it loads | Cost per load |
| --- | --- | --- | --- |
| ponytail | On | Hooks: SessionStart, SubagentStart, UserPromptSubmit | ~900 tokens of rules + ~500 tokens codebase map per session; rules again in every subagent |
| pstack | On | Opt-in. Every skill except `setup-pstack` has `disable-model-invocation: true` | Nothing until typed |
| caveman | On | Reply style every turn | Small |
| superpowers | Off (disabled 2026-11-04) | Was: "invoke a skill before anything, brainstorm first" | None |
| mattpocock-skills | Off (disabled 2026-11-04) | Was: tdd, code-review, codebase-design | None |

What each one writes outside the repo:

- ponytail: one row per turn in `~/.config/ponytail/band/<project>.csv`, a rebuilt
  `~/.config/ponytail/band/board.html`, flags `~/.claude/.ponytail-active`,
  `~/.claude/ponytail-modes/<hash>`, `~/.claude/.ponytail-band`. Webhook empty, so nothing leaves the machine.
- pstack: only `/pstack:setup-pstack` writes a global file, `~/.claude/rules/pstack-models.md`.
  Not run yet. Other skills write into the repo or scratch (noted per skill in section 5).

---

## 2. Which command for which job

| Job | Command | Cost |
| --- | --- | --- |
| Review a change before commit | `/ponytail-review` | 1 agent |
| Review a change where a missed bug costs most | `/pstack:interrogate review-start..HEAD` | 2+ agents, one worktree each |
| Clean up a fresh diff | `/simplify` (built in) | 1 pass |
| What could this small change break elsewhere | `/pstack:blast-radius` | 0 agents |
| Find what to delete, merge, split in a folder | `/ponytail-audit <folder>` | 1 agent, changes nothing |
| Simplify a module, behavior fixed | `/pstack:poteto-mode refactor <area>. keep behavior. end shorter.` | medium |
| Reshape architecture | `/pstack:architect with checkpoint: <what>` | 3-8 agents |
| Pick between designs | `/pstack:arena <task>` | 2 runners + 1 judge |
| Many parallel checks, one report | `/pstack:swarm <slices>` | N agents |
| Vet a measured number (ATE, mm, ms/frame) | `/pstack:benchmark-checklist` | 0 agents |
| Understand a subsystem | `/pstack:how <question>` | 1-5 read-only agents |
| Why is code this way | `/pstack:why <question>` | 1-2 agents here (git only) |
| Make a prompt deeper before a big spec | `/pstack:sharpen <prompt>` | 0 |
| Clean AI tells from prose | `/pstack:unslop` | 0 |
| Last reply too dense | `/pstack:bro` | 0 |
| Back from a long run | `/pstack:ketchup` | 0 |
| Overnight decision log | `/pstack:show-me-your-work` | 1 reviewer at the end |
| Stop agents repeating a mistake | `/pstack:correct <the mistake>` | 0, one commit per class |
| Two fixes on one assumption failed | `/pstack:principle-attack-the-premise` | 0 |
| List deferred shortcuts | `/ponytail-debt` | 0 |

Architecture order: `/ponytail-audit` first (cheap, finds the problems), then
`/pstack:architect with checkpoint`, then put the approved design in a spec in `docs/specs/` for a
fresh session.

### Reviewing on main without PRs

Uncommitted changes are already a diff; every review command defaults to them. For committed work,
mark a start point, list the range, review it:

```
git tag -f review-start
```

```
git log --oneline review-start..HEAD
```

```
/pstack:interrogate review-start..HEAD
```

Worktrees only matter when two agents edit the same files at once. `arena`, `interrogate` and
`swarm` make their own and clean up. For a whole session in its own worktree: `claude -w <name>`,
then fast-forward main.

---

## 3. pstack in Claude Code

- Type every skill as `/pstack:<name>`. Its two agents are `pstack:poteto-agent` (writes code and
  does helper tasks during `poteto-mode`) and `pstack:comment-sicko` (hunts comments and workaround
  code, used by `no-comments`).
- When one pstack skill runs another, Claude reads `<pstack>/skills/<name>/SKILL.md` and follows it.
  The `Skill` tool refuses most pstack skills, so this is expected.
- Each skill reads `docs/harness/claude-code.md` once per session. It maps Cursor names:
  `Task` is `Agent`, `readonly` is `Explore` plus "do not edit", cloud agents are
  `isolation: "worktree"`, `resume` is a new agent with the old result pasted in.
- Cursor-only steps (Automations, Bugbot, cloud-agent dashboards, Custom Mode) are skipped with a line
  `Skipped in Claude Code: <step>. <reason>.`
- Models: roles that default to Grok run on the session model here. Section 8 has the fix.

---

## 4. pstack catalog

All pstack skills in poteto's five groups. **Use** says how often I reach for it; skills marked
"often" or "sometimes" have notes in section 5.

### How you work

| Skill | What it does | Use |
| --- | --- | --- |
| `poteto-mode` | Concise, detailed replies; deliberate subagents; simple code; verified work. Picks one of 23 playbooks | Sometimes, only for a named playbook (section 6). Heavy as a default |
| `poteto-help` | Setup, mode choice, which skill or principle fits a task | Skip: this file does the same |
| `setup-pstack` | Which models each role uses, at what reasoning budget | Once (section 8) |
| `automate-me` | Turns how I work into a personal mode skill, opens a PR | Skip: memory + `~/.claude/CLAUDE.md` already do this |
| `recall` | Brief of where I left off | Sometimes |
| `ketchup` | What changed since my last message, plus decisions waiting on me | Often |
| `ketchup-video` | Same catch-up as a short subtitled slide video | Skip: video in a terminal |
| `bro` | Last message in plain language | Often. No args, no cost |
| `in-your-own-words` | Restates my goal and the problem I am solving | Sometimes, before a big task: catches a misread for one message |

### Design before code

| Skill | What it does | Use |
| --- | --- | --- |
| `architect` | Types, signatures and module shape before implementation | Sometimes, always `with checkpoint` |
| `arena` | Several candidates at once, then grafts the strongest parts into one base | Sometimes |
| `swarm` | Fans out workers, returns one report | Sometimes |
| `figure-it-out` | Auditable playbook for a large or multi-part change | Sometimes; `poteto-mode` routes here for big or unattended work |
| `sharpen` | Makes the task deeper, then rewrites the prompt | Often, before a big spec or run |
| `show-me-your-work` | Decision log (what, why, evidence, result) | Sometimes, long runs |
| `how` | How a subsystem works, where something should live | Sometimes |
| `why` | Design rationale with evidence from git, issues, docs, chat | Sometimes (git only here) |
| `teach` | Plain explanation of a body of work | Sometimes |

### Prove it

| Skill | What it does | Use |
| --- | --- | --- |
| `tdd` | Failing test first, when I ask or the bug has a cheap local test | Sometimes |
| `interrogate` | Adversarial review; only findings proven by a run survive | Often |
| `blast-radius` | What a change could break elsewhere, checked by running code | Often |
| `benchmark-checklist` | Vets a speedup or regression before I trust the number | Often |
| `statechart` | TLA+ model drawn as a statechart, shortest path to each broken state | Skip: needs `mise` (not installed); fits concurrency code, not numerics |
| `create-` / `maintain-verification-skill` | A project skill that drives the app like a user | Sometimes |
| `create-` / `maintain-formal-verification-skill` | Formal checks where a bug costs most | Skip: same as `statechart` |
| `correct` | Makes a repeated agent mistake impossible (architecture, types, lint, then a test) | Often |

### Writing and review

| Skill | What it does | Use |
| --- | --- | --- |
| `technical-writing` | Docs, RFCs, READMEs, PR text | Skip: my docs rule in `~/.claude/CLAUDE.md` covers it |
| `unslop` | Cuts AI tells from writing | Often |
| `no-comments` | Comment Sicko deletes comments and workaround code | Skip: deletes nearly all comments; I keep comments on lines I did not change |
| `typescript-best-practices` | Applied when reading or editing TypeScript | Skip: TS only (viewer, editor), and it does not auto-load here |
| `reflect` | Three reviewers over the transcript; each learning routed into an existing skill | Sometimes |

Not in poteto's list: `make-bot-ui` (Grok Bot only, skip) and the 24 `principle-*` skills (section 7).

---

## 5. Skill notes

Same order as the catalog. Only skills I use.

### How you work

#### `ketchup`
- Read-only. One opening line naming what waits on me, one bullet per thing I asked for, then every
  pending decision with the agent's pick, evidence and risk. Under ~150 words for two items.

#### `recall`
- Rebuilds context from my past transcripts (default last 7 days, this workspace only) plus git.
  Status tags like `[merged]`, `[verified, uncommitted]`, `[planned, not started]`.
- Transcripts live in `~/.claude/projects/<cwd-slug>/`, for example
  `~/.claude/projects/-home-john-tree-perception/`.

### Design before code

#### `architect`
- **Steps:**
  1. Ground: runs `how` over the touched code, `why` if ownership moves.
  2. Sketch: runs `arena`; at least two structurally different whole designs; caller usage written
     first, types derived from it.
  3. Screen each against the red flags below. Prefer the design that hides the most behind the
     smallest interface.
  4. Agree: only with "with checkpoint". Without it, it goes straight to code.
  5. Implement against the sketch; surface deviations.
  6. Scrap: if the same workaround keeps appearing (casts, special cases, "we need a lock"), throw
     the sketch out, subtract first, sketch again.
- **Red flags:** shallow module (big interface, little hidden); information leakage (one decision in
  several modules); temporal decomposition (load/validate/save modules repeating one representation);
  pass-through methods; split ownership (two writers of one state); two ways to do one task;
  importable internals; hand-synced lists.
- **Output:** a types-and-signatures file or module map, plus a rationale (Problem, Usage, Shape,
  Synthesis decision, Tradeoffs, Alternatives, Open questions, Next step). I move it into a spec.

#### `arena`
- **Steps:** private rubric (3-6 criteria the candidates never see); N runners in one message, each in
  its own worktree or `/tmp/arena-<slug>/candidate-<n>/`; one read-only judge from a different model
  family; coordinator reads every candidate, picks a base, grafts 1-2 things from each loser, verifies.
- Without other model families the judge step is skipped and it says so.
- More candidates: `/pstack:arena this, 5 candidates. the file format is expensive to change later.`
- Second opinion: `ask /pstack:arena for a second opinion on this thread and our approach`

#### `swarm`
- Each worker gets a standalone brief and reports `PASS`, `ISSUES` or `BLOCKED` with evidence. A
  missing slice is a gap, not a pass.
- `arena` = same brief N times, then graft. `swarm` = different slices, or a race with a rule declared
  up front (`first pass`, `rank all`, `best-of`).
- Example: `/pstack:swarm run each preset in presets/ through recon preset --dry-run. one worker per preset. one report.`

#### `figure-it-out`
- Falsifiable definition of done, rigor level, phase list with riskiest first, a harness with a
  baseline, a hypothesis loop (smallest change, measure, keep or revert), verdicts VERIFIED /
  NOT VERIFIED / INCONCLUSIVE, decision log via `show-me-your-work`.

#### `sharpen`
- Names what a top professional would do that I did not ask for, the rawest material they would start
  from, the methods and tools, and an outside check. Rewrites the prompt. Does **not** do the task.
- Example: `/pstack:sharpen write a spec for MID-360 lidar on the Elm sapling helix run`

#### `show-me-your-work`
- TSV with columns `ts, phase, decision, why, evidence, result`. Default `decisions.tsv` in the work
  dir, or `.audit/<task-slug>.tsv`. Append-only via `scripts/log.sh`.
- One row per decision, pivot, revert, blocker, and loop iteration. On resume it writes a `start` row.
- At the end it audits the log against the transcript; a reviewer agent reads it and the reply ends
  with an **Attention** section. Read Attention first.

#### `how`, `why`, `teach`
- `how`: onboarding-level answer (Overview, Key Concepts, How It Works, Where Things Live, Gotchas).
  Simple question = 1 agent; complex = 2-4 read-only explorers plus 1 explainer. Overlaps
  `mn-code-map`; use it for a quick chat answer.
- `why`: confidence-tiered history (Direct, Supported, Inferred, Speculative, Unknown) from git blame,
  `git log --follow`, `gh pr view`. Only the source-control investigator runs here (no Slack, Linear,
  Sentry MCPs). Good for "Why was X set to Y? Does the reason still hold?"
- `teach`: runs `how` + `why`, explains with step-by-step diagrams. Overlaps `mn-explaining-new-topics`.

### Prove it

#### `tdd`
- Failing test first, confirm it fails for the right reason, smallest fix, rerun. Prefers no test over
  a brittle mocked one.

#### `interrogate`
- **Steps:** states the intent (via `in-your-own-words`); one adversary per reviewer entry, each in its
  own worktree with my uncommitted changes copied in; each proves a finding with a command and its
  output; reruns every finding; keeps only ones that break the intent; merges same root cause.
- **Output:** Intent, Findings (command, output, expected, who found it), Dropped list with reasons.
  Applies no fixes. Drops style, naming, structure, "a future change could break this".
- **Scope:** what I name, else the branch diff plus working tree. On main with nothing named that is
  uncommitted changes only, so name a range.
- Example: `/pstack:interrogate review-start..HEAD, skeptically. no nitpicks unless it's a real bug or regression.`

#### `blast-radius`
- **Steps:** read the change; find the one fact it is safe because of; look where grep stops (library
  source, file formats, JSON/MCAP/rrd readers, other languages, flags, three hops away); list risks
  with likelihood and cost; prove the one fact with a script and paste the output.
- **Certainty ladder:** 1 "you said so" (worthless), 2 `file:line`, 3 showed the bad case can't happen,
  4 ran it, 5 reproduced in the running app.
- **Use for:** shared code: `recon_harness` data model (Frames, Trajectory, FrameIndex), `treesim`
  solver, `bp` Estimator. A big change runs itself as an `arena`.

#### `benchmark-checklist`
- **Use for:** ATE, mm error, ms/frame, speedups, any "X beats Y" metric. Catches lucky-draw baselines
  (the survey-drag 27 mm one would have failed question 5).
- **Seven questions, each needs run evidence:**
  1. Why not double? Name the limiter.
  2. Did every side run tuned as it would for real?
  3. Does it break a physical limit (bandwidth, cores, Amdahl)?
  4. Did anything error or give wrong output?
  5. Does it reproduce? At least 5 runs per side, alternating A B A B, median and range. A gap smaller
     than run-to-run spread is "no difference". Treat seeds as runs.
  6. Does it matter end to end?
  7. Did the work run inside the timed or scored region?
- **Verdict:** faster, slower, no measurable difference, or inconclusive. Inconclusive when the limiter
  is unnamed, a side was untuned, or 4 and 7 were not checked.

#### `create-verification-skill`
- Interviews the repo, not me: what users touch, how it launches, what can drive it (existing harness
  first, then browser/CDP, PTY, HTTP), what evidence proves behavior, whether two instances fit side
  by side.
- Writes `.claude/skills/verify-<app>/SKILL.md` (Launch, Doctor, Drive, Evidence, Cleanup, Helpers)
  and `features/README.md` plus one file per top 3-5 features.
- Proves itself once: launch, doctor, drive one feature, capture evidence, clean up, check the evidence
  survived. Never kills by process name.
- Targets: skeleton editor (`:8770`), `treesim` viewer (`pixi run lemon`, `:8767`), `recon` CLI,
  `bp run`. Evidence = metrics JSON, `.rrd` files, screenshots via browser-harness.
- Then: `/pstack:poteto-mode fix <bug>. repro with /verify-<app> first. show me before/after screenshots.`
- `maintain-verification-skill` keeps it current: one read-only agent per feature, one live pass; ends
  `clean`, `changed` or `blocked`; never edits product code.

#### `correct`
- **Steps:** mines commits, reverts, review comments, workaround comments; groups mistakes into classes
  (a class needs 2 occurrences); fixes each at the highest level that works:
  1. architecture or data structure (mistake impossible),
  2. types, or a lint or CI check whose error names the fix,
  3. a test,
  4. a doc or agent rule (last: nothing fails when it is skipped).
- Proves each new check fails on a real past mistake. One commit per class. Keeps a rule-to-enforcer
  table in `AGENTS.md` (no project `CLAUDE.md`).
- Example: `/pstack:correct agents start heavy GPU jobs without the heavy.sh wrapper`

### Writing and review

#### `unslop`
- **Use for:** READMEs, explainer pages, spec prose, commit bodies. Prose only;
  `human-maintainer-pass` covers code.
- **Rules (stable ids):** 3 "-ing" filler phrases. 5 vague attributions. 7 AI words (crucial, delve,
  pivotal, showcase, underscore...). 8 "serves as" for "is". 9 "not just X but Y". 10 forced threes.
  11 synonym cycling. 12 false ranges. 13 no em dashes, en dashes or parentheses. 14 no mid-sentence
  colons. 15 bold overuse. 16 "**Label:** label repeated" lists. 17 sentence-case headings.
  18 emojis. 19 curly quotes. 20 chatbot phrases. 22 sycophancy. 23 filler ("in order to").
  24 over-hedging. 25 generic conclusions. 26 metaphor nouns (substrate, vector, harness, surface,
  north star...). 27 say what it does, not how it feels. 28 split dense sentences. 29 active voice.
  30 cut adverbs. 31 plain word. 32 no aphorisms or personified code. 33 no over-compression
  (dropped articles, fragments, arrows).
- Rule 26 "harness" means the metaphor; `recon_harness` is a name and stays. Rule 33 is the opposite
  of caveman, which is fine: caveman is for chat, unslop is for docs. Rule 24: see section 11.
- Example: `/pstack:unslop the readme changes, no em dashes, keep meaningful hedges`

#### `reflect`
- 3 reviewers (judgment, tooling, divergent) plus a synthesizer read this transcript and sort
  proposals into Accepted, Rejected, Backlog. Waits for my approval. Edits copies under
  `.claude/skills/`, never the plugin cache.
- Approve only what would change a future decision. One odd session is an anecdote.

---

## 6. `poteto-mode` and its playbooks

`/pstack:poteto-mode <task>` picks one of 23 playbooks, copies its steps into the todo list, runs the
other skills as steps fire, and names the principles it applied. A skipped step stays as
`skip: <reason>`. It has its own reply rules (whole short sentences, no em dashes, an evidence label
on every claim); they override caveman for that task.

**A good prompt has up to five parts:** goal; a done check that can pass or fail; the proof I want
(command output, numbers before/after, screenshot); what I know (symptom, log, run dir); constraints
("repro first", "don't change any code yet", "zero behavior change", "let me review before
proceeding"). Leave out the how and my theory of the cause. Do not list skills; the playbook orders
them.

**Pitfalls from the guide:**
- A duration is not a finish condition. Give a check, not "work for 4 hours".
- "new task" plus "don't change any code yet" forces a fresh match; otherwise it treats a question as
  the next step of the current task.
- Parallel agents in one checkout overwrite each other. Say "own worktree per attempt".
- Do not edit a skill mid-task because it misbehaves. Fix it separately.

### Playbooks that fit me

| Playbook | Trigger | What it does | Example |
| --- | --- | --- | --- |
| Investigation | Read-only question | `how` (+`why`), cited answer or tradeoffs table, no code | `/pstack:poteto-mode investigate why still-cam sway is chaotic. what we know, what data you used, hypotheses. don't change any code yet.` |
| Bug fix | A defect | Reproduce first; binary-search the cause; fix; verify on the same surface; failing repro committed before the fix | `/pstack:poteto-mode SmartQSM OOMs after heavy nodes. repro first, then fix. show memory before/after.` |
| Perf issue | Measured slowness | Baseline trace; mantras in order (don't do it, not again, less, later, concurrently, cheaper); before/after with `benchmark-checklist` | `/pstack:poteto-mode bp run takes 287 ms/frame. trace it, fix the measured cause, show before and after.` |
| Hillclimb | Push one metric | Frozen harness, one hypothesis at a time, keep wins (one commit each), revert the rest, `decision.tsv` | `/pstack:poteto-mode hillclimb survey-drag error. target 20 mm, at least 10 iterations, median over 5 seeds.` |
| Runtime forensics | Live symptom (leak, spin) | Capture, reduce, prove mechanism, map to `file:line`. Diagnosis only | |
| Trace forensics | A captured profile or trace | Load into sqlite, narrow, attribute to source. Diagnosis only | `/pstack:poteto-mode here's a py-spy profile. where does the time go, which lines own it. no fix yet.` |
| Feature | New behavior | `how`, `architect`, throughput checkpoint, delegate, verify, interrogate if contested | |
| Refactoring | Same behavior, new structure | Pin behavior; name target shape; subtract first; small steps; migrate callers and delete old API together; prove unchanged; revert if reader load did not drop | `/pstack:poteto-mode refactor recon_harness sinks. zero behavior change. pin = pixi run test + one smoke run, no goldens. end shorter.` |
| Prototype | Settle a design by running it | Throwaway variants in a scratch dir behind one switcher, evidence, recommendation | `/pstack:poteto-mode prototype three registration inits for the lemon twin. show error and runtime for each.` |
| Session pickup | Take over earlier work | Reads the trail, reconstructs state, names the resume point, verifies inherited claims | `/pstack:poteto-mode take over this work. read the decision log, figure out what's done, continue. don't redo finished work.` |
| Pause safely | I need to stop | Safe boundary, one `wip:` commit, resume note | `/pstack:poteto-mode pause safely` |
| Autonomous run | Long run to a checkable goal | Each iteration: smallest change, verify, commit or discard, log a row; plateau means pivot, never relax the goal | see section 9 |
| Multi-phase plan | Work across phases | Plan with per-unit verify blocks. I use my own spec format instead | |
| Eval | Test a skill or prompt change | Blind candidates, one blind judge | `/pstack:poteto-mode run the eval playbook on this skill change. same task for both variants.` |
| Worktree cleanup | Disk full | `df -h`, audit script, pauses on uncommitted work, prunes the rest | `/pstack:poteto-mode what's eating my disk? prune the worktrees that are safe to prune.` |

Skipped (PR, Cursor or team flow): Opening a PR, Babysit, Shipping, Autopilot-full, Autopilot-stack,
Orchestrate, Visual parity, Authoring a skill (uses Cursor's `create-skill`).

---

## 7. The 24 principles

Standing rules, not commands: data structures first, guards only at boundaries, delete before you
add, smallest change, prove the real artifact, and encode a repeated correction in a lint or check
instead of another paragraph of instructions. `poteto-mode` and `poteto-agent` apply them on their
own. Outside those nothing loads them; steer by name with `/pstack:principle-<name>` or "apply
prove-it-works" in a prompt.

| Principle | Apply when | Rule | Fit for me |
| --- | --- | --- | --- |
| laziness-protocol | Refactoring, sizing a diff | Smallest change, one source of truth, fewer lines | High |
| subtract-before-you-add | Before adding or rewriting | Delete dead code and redundant checks first | High |
| minimize-reader-load | Code hard to trace | Collapse one-caller wrappers; a new reader answers "where does X come from" in 30 s | High |
| attack-the-premise | 2+ fixes on one assumption failed | Write the assumption as one sentence; test it with an observation that differs if it is false; no third fix first | High |
| explain-the-number | Before trusting a number | Name the limiter; rule out other causes; keep run count and spread | High |
| prove-it-works | Before saying done | Check the real artifact, not "it compiles" | High |
| fix-root-causes | Debugging | Ask why until it is a wrong decision; a guard is a fix only for a legitimate state | High |
| build-the-lever | Any non-trivial work | Build the script that does or proves it, rerunnable | High |
| encode-lessons-in-structure | Same instruction written twice | Turn it into a lint, check or script | High |
| never-block-on-the-human | Asking about reversible work | Do it, then show it | High |
| model-the-domain | Branchy stateful code | State machine, typed model, table; a second boolean synced to a first is the tell | Medium |
| foundational-thinking | Before logic | Data structures first; three similar lines beat a premature abstraction | Medium |
| redesign-from-first-principles | New requirement | Build as if it were there from day one, do not bolt on | Medium |
| sequence-verifiable-units | Multi-step work | Each unit ends green before the next; order commits so they prove themselves | Medium |
| boundary-discipline | Validation, errors | Validate at the edge, trust typed internals | Medium |
| exhaust-the-design-space | No precedent | 2-3 prototypes side by side | Medium |
| guard-the-context-window | Context filling | Bulk reading goes to subagents | Medium |
| outcome-oriented-execution | Planned rewrite | Converge on the target, no throwaway compat | Matches "scorched earth" |
| migrate-callers-then-delete-legacy-apis | New internal API | Move callers and delete the old API in one wave | Matches "no compat" |
| test-behavior-not-implementation | Writing a test | Test fails when behavior breaks, passes when internals change | Matches "tests through the seam" |
| make-operations-idempotent | Commands that rerun after crashes | Run twice, crash anywhere, still converges | Pipelines, sessions |
| separate-before-serializing-shared-state | Concurrent writers | Give each writer its own file or key first; "we need a lock" is a smell | Parallel agents |
| experience-first | UX tradeoffs | Fewer polished features | Viewers, editor |
| type-system-discipline | Typed code | Illegal states unrepresentable | Low (Python) |

---

## 8. pstack model setup (not run yet)

Defaults send code roles to Grok. Claude Code cannot run Grok, so those roles run on the session
model, and Opus roles run `opus xhigh`. Effect: `arena`, `interrogate` and `architect` panels are all
Claude, and the "judge from a different model family" rule cannot hold.

`/pstack:setup-pstack` asks a budget (unlimited = max, large = xhigh (default), medium = high,
small = medium), shows each role, and writes `~/.claude/rules/pstack-models.md`. It applies in new
sessions. Delete a role line to restore its default; delete the file to restore all.

| Role | Default (Claude Code value) | My pick (from my subagent-model rule) |
| --- | --- | --- |
| `feature, refactoring` | inherit-parent (Grok) | opus |
| `bug-fix` | inherit-parent | opus |
| `perf-issue` | inherit-parent | opus |
| `hillclimb` | inherit-parent | opus |
| `judgment and prose` | opus xhigh | fable |
| `hardest tasks` | opus xhigh | fable |
| `how explorer` | inherit-parent | sonnet |
| `how explainer` | opus xhigh | opus |
| `why investigators` | inherit-parent | sonnet |
| `why synthesizer` | opus xhigh | opus |
| `reflect tooling` | inherit-parent | sonnet |
| `reflect judgment, divergent, synthesizer` | opus xhigh | fable |
| `arena runners` | opus xhigh + inherit-parent | opus + fable |
| `arena cross-judge pool` | opus xhigh + inherit-parent | fable |
| `swarm workers` | inherit-parent | sonnet |
| `architect runners` | opus xhigh + inherit-parent | opus + fable |
| `interrogate reviewers` | opus xhigh + inherit-parent | fable + opus |

Opus + Fable on panels gives two different models, so the reviews disagree in useful ways.

---

## 9. Overnight and unattended runs

**Trust first.** Loop only when all four hold: I did the task once or watched it; the agent has my
tools (verification skill, logs); every stage can stop the line; I read a few transcripts and turned
repeat failures into checks.

**The contract prompt:**

```
/pstack:poteto-mode im going to bed. <task> in a fresh worktree off main.
done means <checkable predicate>.
keep a decision log. don't ask me before committing.
/loop until done. if you're truly stuck after a few hours, stop and write up why.
```

- "done means" must be a check, not a duration.
- Each iteration: check the goal, smallest change, verify on the real artifact, commit or discard,
  log one row. A plateau means pivot. The goal never quietly relaxes.
- My rules still apply: GPU runs detached (`setsid nohup`), heavy jobs through `heavy.sh`, `nice 19`.
  Put them in the prompt.
- Afterward fast-forward main to the worktree branch.

**Morning:** read the Attention section first, then the rows it points at. Or `/pstack:ketchup` in the
chat that ran it.

```
/pstack:show-me-your-work catch me up on what you did last night
```

**Pause and resume:** `pause safely` writes a `wip:` commit plus a resume note. A fresh chat resumes
with the Session pickup prompt in section 6.

---

## 10. ponytail

### What it injects every session and every subagent

"Lazy senior developer. The best code is the code never written." Rules:

- **Before writing:** read the task and the code it touches; list every place the change must reach
  (callers, tests, fixtures, config, exports); check what it could break.
- **Ladder, first that fully works:** 1 does it need to exist (name skipped extras in one line);
  2 already in this codebase; 3 standard library or platform; 4 installed dependency (never add one
  for a few lines); 5 one line; 6 minimum code.
- Lazy about the solution, never about the change: finish callers, tests, fixtures.
- No abstraction, wrapper, option, config or "for later" code nobody asked for. Keep the codebase's
  layers and conventions.
- Bug fix: grep every caller, fix the root cause once in shared code. Moved code keeps its error
  handling.
- New non-trivial logic (branch, loop, parser) leaves one small test or `assert`.
- Known limit gets a comment: `shortcut: <the limit>, <when to upgrade>`.
- Never cut: validation at trust boundaries, error handling that prevents data loss, security,
  accessibility, hardware calibration, anything I asked for.
- Every reply ends with one or two lines: what was skipped or unchecked, any risk.

It also injects a ~2000-character codebase map (top-level functions per folder). Turn off with
`PONYTAIL_MAP=0`.

### Levels and toggles

| Input | Effect |
| --- | --- |
| `/ponytail lite` | Builds what I asked, names the smaller option in one line |
| `/ponytail full` | Default rules |
| `/ponytail ultra` | Also pushes back on parts of the request the need does not justify |
| `/ponytail off` or the whole message `stop ponytail` / `normal mode` | Off for this project's sessions |
| `/ponytail` | Shows the level, or turns it back on |
| `/ponytail default lite` | Writes `~/.config/ponytail/config.json`; new sessions start in that level |
| `/ponytail band`, `band on`, `band off` | Show or hide the status band |
| `/ponytail band import` | Backfill the cost ledger from past transcripts |

Mode is per project (all sessions in one repo share it). Level switches only by slash command.

### `/ponytail-review`

- **Scope:** what I name; else uncommitted changes; else the last commit. Takes `staged`, `branch`,
  a PR link, files.
- **Steps:** read the diff, then callers, callees, tests; grep every caller on a signature change;
  state the assumed load. Looks for, in order: Bug, Risk, Scale, Missing test, Speed, Lean (delete,
  reuse, stdlib, yagni, merge, split). It reads code outside the diff, so it catches an untouched file
  that now breaks.
- **Output:** `What this change does:`, then findings grouped **Must fix / Should fix / Nice to have**,
  each with `file:L<a>-<b>` and four bullets: What this is, Problem, Fix, If we skip it. Ends with
  `Verdict: Ship.` or `Verdict: fix 1 and 3 first.`, `Lean: -<N> lines possible.`, `Not checked:`.
- No style taste, no "consider". A `shortcut:` comment that names its limit counts as a decision.

### `/ponytail-audit <folder>`

- Same six categories as review, whole folder or repo. Reads user-input, write, job and shared-state
  paths fully. Greps the whole tree (tests, config, strings) before calling code unused.
- **Output:** `What this repo does:` plus assumed load, at most 20 findings in the same format,
  `Verdict:`, `Lean: -<N> lines, -<M> dependencies possible.`, `Not checked:`.
- Changes nothing. Example: `/ponytail-audit recon_harness/`

### `/ponytail-debt`

Lists every `shortcut:` comment as `file:line, what was simplified. ceiling: <limit>. upgrade: <trigger>.`
Flags ones with no trigger. Takes another marker: `/ponytail-debt TODO`.

### The band (status line)

Shows level, session cost, last-turn cost, agent time, `% reuse` (share of new calls that hit code
that existed at session start), `⚠ N callers open` (a removed or renamed function still called),
test status (`✓ N tests`, `✗ N failed`, `no test since change`), and buttons Review, Audit, Board,
Details. Board opens `~/.config/ponytail/band/board.html`. "Callers open" and "no test since change"
are the useful live warnings.

### Benchmark (author's own)

39 tasks, 5 runs each, Opus 5.5, `claude -p`, no shell. Versus no skill: lines −53%, output tokens
−45%, cost −26%, time −41%, tests where logic needs one 98% vs 68%. Stated limits: safety is level
with no skill (not better); 21 of 39 tasks measure size only; reply preference vs no skill not
significant; author-run with Claude judges, no outside replication. `/ponytail-gain` shows these
benchmark numbers, not numbers for this repo.

---

## 11. Clashes with my rules, and what to say

| Clash | What to say or do |
| --- | --- |
| pstack panels are all Claude (Grok roles fall back) | Run `/pstack:setup-pstack` with section 8 picks |
| Refactoring playbook pins behavior with a golden snapshot; I want no goldens | "pin = `pixi run test` + one smoke run, no goldens" |
| Code playbooks end with "Opening a PR"; I commit on main | "commit on main, no PR" |
| `architect` goes straight to code by default | Always "with checkpoint"; the design goes into a spec |
| `correct` and `reflect` write rule tables or skill edits | Fine; the table lands in `AGENTS.md` |
| `unslop` rule 24 cuts hedges that carry meaning | "keep meaningful hedges (may, likely, untested)" |
| `swarm` and `arena` start many agents at once | Put the heavy-jobs rule (≤ 3 heavy, `nice 19`, `heavy.sh`) in the prompt |
| ponytail keeps the existing layers; I sometimes want a rewrite | "big-bang rewrite, no compat", or `stop ponytail` for that session |
| ponytail adds one test per new branch or loop; I want tests through the seam only | Say "tests through the seam only" once |
| ponytail `shortcut:` comments | Fine: they name a limit and a trigger, no dates or spec ids |
| ponytail rules load into every subagent (~900 tokens) | Harmless; scope with `PONYTAIL_SUBAGENT_MATCHER` if it matters |

---

## 12. Copy-paste commands

Shell commands. Run `/reload-plugins` in Claude Code after any of them.

Update pstack (third-party marketplaces do not auto-update):

```
claude plugin update pstack@cursor-plugins
```

Turn superpowers or mattpocock-skills back on:

```
claude plugin enable superpowers@claude-plugins-official
```

```
claude plugin enable mattpocock-skills@claude-plugins-official
```

Turn ponytail off or on:

```
claude plugin disable ponytail@ponytail
```

```
claude plugin enable ponytail@ponytail
```

Remove pstack's model rule (back to defaults):

```
rm ~/.claude/rules/pstack-models.md
```

---

## Sources

- poteto, "The Complete Guide to pstack Pt. 1", 2026-08-31: https://x.com/poteto/article/2094457600259842065
- pstack source: https://github.com/cursor/plugins/tree/main/pstack
- Local pstack: `~/.claude/plugins/cache/cursor-plugins/pstack/0.15.36/` (skills, `docs/guide/` ch. 1-10,
  `docs/harness/claude-code.md`)
- Local ponytail: `~/.claude/plugins/cache/ponytail/ponytail/5.3.3/` (skills, hooks, README,
  `benchmarks/results/2026-10-07-agentic.md`)
