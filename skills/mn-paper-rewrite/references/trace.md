# Trace: the mechanism in chat

One concrete example travels from raw input to final output. At each stage,
say what goes in, what changes, and how it reaches the next stage. The shared
rules of `SKILL.md` apply: read all of the source, carry one running example,
mark where statements come from, hunt the glue facts.

The ladder below sets the structure, and it wins over a general reply-length
rule (for example a five-sentence cap). Keep plain, complete sentences and
define each term at its first use.

If the paper sits in a project repo, read the project spec or README first, so
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
9. What comes out, and how good is it? The output, results on held-out data
   next to results on fit data, and what the evidence does not show.
10. Our version: how it maps onto my project, and what we do differently.

End a full walkthrough with "Restate check": a "so basically" paraphrase of
the whole pipeline in 4 to 6 lines for me to accept or correct. Add the one or
two wrong restatements a newcomer most often makes, each with its correction.

When I ask for the trace as a page, write the rewrite page of
`references/page.md` instead: its sections hold the same rungs.

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
5. Each claim points to a section, figure, table, or `file:line`.
6. Each follow-up reply starts with "Yes", "Yes, with N corrections", or
   "Not quite".
