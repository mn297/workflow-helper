---
name: mn-tracing-papers-end-to-end
description: >
  Trace a paper, method, or system end to end with one running example, in
  the order the user thinks: purpose, machinery, unknowns, timeline, inputs,
  objective, the path from unknown to objective, picture, evidence. Triggers:
  the user asks how a paper or method actually works. The user asks "what is
  the sequence", "what is it learning" or "where does X enter the loss". The
  user restates a pipeline ("so basically they ...") to test it. For a saved
  notes file, use mn-writing-plain-paper-notes. For a concept with no
  pipeline behind it, use mn-explaining-new-topics.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Papers, Explanation, Walkthrough, Mechanism"
  category: "writing"
---

# mn-tracing-papers-end-to-end

I understand a method by tracing it. One concrete example travels from raw
input to final output. At each stage I ask what goes in, what changes, and how
it reaches the next stage. Papers follow the order of their claims, because
they are written for reviewers. Rewrite them in the order the data flows.

Me: robotics and simulation engineer, reinforcement learning at Spinning Up
level, often new to the subfield of the paper.

The ladder below sets the structure of a walkthrough, and it wins over a
general reply-length rule (for example the five-sentence cap of
simple-english). Keep plain, complete sentences and define each term at its
first use.

## Before you answer

1. Read the source: the method section, the algorithm boxes, the appendix,
   and any code. The code holds the glue that papers leave
   out: truncated gradients, loss terms that are switched off, clamps,
   integer casts. When paper and code disagree, follow the code and say so,
   with file:line.
2. Pick the running example: the paper's own case with its real numbers
   (point counts, parameter counts, time steps, results). Use it on every
   rung. Label an invented example as illustrative.
3. If the paper sits in a project repo, read the project spec or README, so
   rung 10 maps onto real work.

## The ladder

Answer in this order, one numbered section per rung, each with a question
header. Each rung opens with one bold answer sentence, then the details on the
running example. If a rung does not apply, say so in one line and move on.

1. What is it for? The purpose of the method, and how it touches my project.
2. What actually runs? The engine, model, or code at the core: what it knows,
   what it does not know, and what it is built on.
3. What is unknown? What the method learns or estimates, at what granularity
   (one per element, per region, or global), and how many values, with the
   running example's count.
4. In what order does it happen? The timeline from raw data to output, as a
   numbered list. Mark each step as once (preprocessing), repeated (the
   training or solve loop), or use time. Mark what stays fixed and what
   changes.
5. How does the world act on it? Inputs, actuation, boundary conditions, and
   conditioning: who moves what, the moment that link is made, and whether
   it changes later.
6. What is compared to what? The objective: each term as an equation with
   every symbol defined, plus one number worked through ("a 2 cm miss costs
   0.5 × 0.02² = 0.0002").
7. How does the unknown reach the objective? The causal or gradient chain,
   link by link, from one unknown to the objective. Write the chain rule or
   the data flow explicitly, and name every truncation, detach, or clamp.
8. What does it look like? A diagram of rung 7: an ASCII sketch in chat, an
   inline SVG on a page.
9. What comes out, and how good is it? The output artifact, results on
   held-out data next to results on fit data, and what the evidence does not
   show.
10. Our version: how it maps onto my project, and what we do differently.

## Glue facts

A glue fact is an identity or link that experts leave unsaid because it is
obvious to them. Examples: "the first 1,630 particles are the tracked
points", "the hand acts only through springs built at frame 0". Hunt them,
and state each one on the rung where it is first needed. These are the places
where I get stuck.

## Follow-ups

I learn by restating. When I write "so basically they ..." or ask a short
follow-up:

- Start with "Yes", "Yes, with N corrections", or "Not quite". Then fix one
  wrong assumption at a time, in ladder order.
- Answer on the rung the question belongs to, and continue from there.
- Keep the running example and its numbers.

End a full walkthrough with "Restate check": a "so basically" paraphrase of
the whole pipeline in 4 to 6 lines for me to accept or correct. Add the one or two wrong
restatements a newcomer most often makes, each with its correction.

## Output

Chat by default. When I ask for a page or an artifact, load artifact-design
and follow mn-organizing-project-docs. For rung 8, also load
artifact-diagramming. Keep the ladder as the section order.

## Example (PhysTwin, abbreviated)

Rung 3: "**PhysTwin learns one stiffness per spring, not per region: 27,655
values for the rope (27,381 object springs and 274 hand springs).**"

Rung 7: "Stiffness never appears in the loss. The loss compares positions, and
the positions come out of 667 substeps that each use the spring force
$F = Y_s (L/L_0 - 1)$. So
$\partial L/\partial Y_s = \sum_i (\partial L/\partial x_i)(\partial x_i/\partial Y_s)$.
The gradient flows back through one frame only, then Adam updates every
spring."

Follow-up. User: "so they scan, place springs, then track?" Answer: "Not
quite. Tracking runs first, on the whole recorded video, before any spring
exists. Frame 0 is the scan ..."

## Self-check

1. Every rung uses the running example and its real numbers.
2. The timeline of rung 4 marks each step as once, repeated, or use time.
3. Rung 7 names each link from one unknown to the objective, with its
   truncations.
4. Each glue fact appears on the rung where it is first needed.
5. Each claim points to a section, figure, table, or file:line.
6. Each follow-up reply starts with "Yes", "Yes, with N corrections", or
   "Not quite".
