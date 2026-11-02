---
name: mn-making-explainer-films
description: >
  Use when the user asks for a video, a film, an animation, a "Remotion style" or "3Blue1Brown
  style" explainer, a motion walk-through, or says that a static page, a code map or a chat
  explanation did not make them understand and they want to see it move: how a pipeline, an
  estimator, a solver or an algorithm works on a real run, to watch in a browser or as a claude.ai
  artifact. Not for an mp4 file (that is Remotion), not for one diagram (artifact-diagramming),
  not for a map of the code (mn-code-map).
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Explainer, Film, Animation, Artifacts, HTML, Docs"
---

# mn-making-explainer-films

A film is one HTML page that plays like a video: a 1280 x 720 stage, a caption under it, a scrub
bar, scene chips. Every scene is a pure function of the frame number, as in a Remotion
composition, with no Node, no render step and no library: `render(frame)` sets the attributes of
elements built once. The viewer plays it, scrubs it, or opens it paused at a frame. A finished film
lives at `~/<project>/docs/<topic>/<film>.html`, with its data script and template in
`docs/<topic>/data/`. If `~/.config/skills/mn-making-explainer-films.local.md` exists, it names a
finished film on this machine; read it before making a new one: it is the model for the arc, the
density of a scene and the captions.

## What a film is made of

1. **The run.** One real run folder and one example followed end to end: one frame, one object,
   one track. The film shows the real pictures the method saw, with the method's own quantities
   drawn over them. A schematic stands in only where no picture exists (a side view of the camera
   and its rays).
2. **The storyboard.** 8 to 10 scenes, 5 to 25 s each, one claim and one picture per scene, in
   the order the data flows: the question; where the data comes from; what the method gets and
   nothing else; each stage with its number; one step traced (for a filter: predict, measure,
   update); the whole run against the truth; the numbers and what is missing. The last scene lists
   the gaps, not a win. `references/storyboard.md` holds a worked storyboard as the model.
3. **The data script**, `docs/<topic>/data/<film>_data.py`, run in the project's environment.
   It writes one JSON: the images as small JPEG data URIs (960 x 540 at quality 70 is 60 to 90 KB
   each; six are enough), series and point lists rounded to 0.1, a sample of the tracks by class,
   one frame's residuals, the per-frame error, the numbers of the log. Every number on the stage
   comes from this JSON; the page computes positions and nothing else. A quantity the run never
   recorded is not drawn. A derived one is labelled derived. An exaggeration says its factor on
   the stage and in the caption ("drawn sixteen times their size").
4. **The page**, from `template.html`: the player, the helpers (`ip` is Remotion's
   `interpolate`; `scene`, `svg`, `text`, `polyline`, `chip`, `lerpPts`) and two example scenes
   to replace. Captions are HTML under the stage, so they wrap on a phone; the stage holds short
   labels and a readout chip (frame, phase, the scene's number). One color per kind of data for
   the whole film, the project's own viewer's colors when it has one. A loupe (a nested `<svg>`
   whose `viewBox` follows the part of interest) when the motion is a few pixels. No CSS
   animation, no timers: the frame drives everything, so a scrub lands on the same picture as a
   play.
5. **The check.** `python3 scripts/build.py template.html data.json page.html` pastes the JSON,
   checks the size and the script's syntax. `bash scripts/shoot.sh page.html shots 100 400 ...`
   screenshots one or two frames per scene with a headless Chromium. Look at every PNG: text cut
   at a chip's edge, labels on top of each other, a drawing spilling out of its card, a scene
   with nothing on it. Fix and shoot again.
6. **The place.** `docs/<topic>/<film>.html`, its data script and template in
   `docs/<topic>/data/`, a card in `docs/index.html`, one line in the README, published as an
   artifact: all per mn-organizing-project-docs. The artifact-design page contract holds (title,
   theme tokens, phone width, CDN list); the template follows it.

## Steps

1. Pick the run and the example. Read its logs and output files. List the numbers the film will
   show, each with the file it comes from.
2. Write the storyboard as a table (scene, seconds, claim, picture, data) before any code. When
   the ask is vague, give the user the table, one line per scene, and go on.
3. Write and run the data script. Check the JSON's size and a few of its values against the log.
4. Copy `template.html`, fill the title, the lede, the sources line and the scenes. Build.
5. Shoot, look, fix. Then place, card, README, publish, commit.

## The template's API

| Call | Does |
|---|---|
| `scene(name, label, seconds, captions, build, render)` | one scene; `captions` is `[[frameWithinScene, text], ...]` |
| `build(g)` | runs once, lazily: make the elements under the scene's group `g`, keep handles on `g` |
| `render(t, g)` | every frame: set attributes for the local frame `t` |
| `ip(t, [a, b], [c, d], ease)` | `c` before `a`, `d` after `b`, eased between |
| `showImage(alpha)` | the run's picture behind the stage, or several keyed by frame |
| `?f=N` or `#fN` | open the page paused at frame N; `shoot.sh` uses it |

## Common mistakes

- Reinventing the player. Agents that build their own player tend to end up with a canvas and
  the captions painted inside it. The template has the player.
- Numbers computed in the page from raw data: the stage and the report then disagree (one
  number on screen, another in the summary, from two formulas). Compute once, in the script.
- An abstract number line or a bar chart where the camera's own image exists.
- A last scene that declares victory. End with the numbers and the gaps.
- A storyboard without "where the data comes from" and "what the method gets": the viewer
  cannot tell measured from truth, which is the point of most perception films.
- Residuals too small to see at true scale and not exaggerated, or exaggerated silently.

## When to use Remotion instead

When the deliverable is an mp4: a talk, a paper, a voiceover, music, a beat-cut edit. The port is
one to one: each `scene` is a `<Sequence>`, `render(t)` reads `useCurrentFrame()`, `ip` is
`interpolate`. The kit is claude-motion (github.com/whaleyxbt/claude-motion): Node 20, ffmpeg,
Chromium. Its `npm run capture` can also film this page as it is.
