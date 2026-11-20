---
name: mn-code-shape
description: >
  Shape of the functions you design or propose: math and geometry as pure
  functions (values in, values out), listing the options kept apart from
  choosing one, code that reads state never writes it, hard limits as filters
  before one cost, and one frame or unit system between functions. Use when
  you propose a new function, helper or API, or sketch code in chat. Not for
  my own drafts: those keep my decomposition.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Functions, Design, Python"
  category: "coding"
---

# mn-code-shape

Before you write a body, write the signatures and the one line where the caller
chains them. If that line reads as data flowing through steps, write the bodies.
If it needs a flag, a tie-break parameter or a shared mutable object to make
sense, reshape first.

## Defaults

1. **Pure where it can be.** Math, geometry and kinematics take values and
   return values. No model, sim state, globals or IO in the signature, unless
   the function needs a lookup only the model holds. The test: you can call it
   with literals alone.
2. **List, then choose.** When a task has a few equal ways to do it (symmetric
   twins, either end, IK branches, mirrors to try), one function returns all of
   them and another picks one. The lister knows the geometry. The picker knows
   the current state. Neither does the other's job.
3. **Readers do not write.** A function that reads state (a sim, a robot, a
   file) returns a value and changes nothing. Only the loop steps, commands and
   writes.
4. **Filters, then one cost.** Hard limits (joint range, reach, collision)
   drop candidates. Then take one `min` over one cost in one unit. Do not add
   weighted terms in different units: the weights decide the answer, and no one
   checks them.
5. **One frame between functions.** Pass values in one shared frame and unit
   system (world frame, SI). A local frame lives inside the function that needs
   it.

## Where it stops

- Only for a few options that are cheap to list. A continuous choice (a grasp
  anywhere along an edge) is an optimisation, not a list.
- Split a function only when it already holds two concerns. The tells: one loop
  both builds and scores, or a parameter exists only to break a tie. Three
  similar lines beat a new helper, and the smallest change still wins.
- My draft keeps my decomposition. Name a shape problem in it in one line; do
  not restructure it.

## Example

Before: one function builds the grasp twins, takes a tie-break angle, reads the
arm and scores, all in one loop.

```python
def pick_roll(m, d, grasp, brick_pos, brick_quat, heading): ...
```

After: geometry in one pure function, the choice in one function that reads
the arm and writes nothing.

```python
def grasp_candidates(brick_pos, brick_quat, grasp) -> list[Pose]: ...  # pure
def easiest(m, d, poses: list[Pose]) -> Pose: ...  # reads the arm, writes nothing

p, q = easiest(m, d, grasp_candidates(c0, q0, END))
```

## Check before you show it

- Each function runs on literals, or its docstring says which state it reads.
- No parameter exists only to break a tie the caller does not care about.
- The final choice is one `min` over one cost.
