---
name: mn-notation-robotics
description: >
  Math notation for robotics docs, derivations and code comments. Every vector
  shows its frame (left superscript) and its reference point (subscript). Every
  letter has one meaning on the page. No letter stands in for an intermediate
  expression. Use it to write or rewrite kinematics, Jacobians, wrenches,
  force-torque sensor maps, dynamics, observers or estimators. Also use it for
  a derivation that reads hard. User phrases: "notation confusing", "which
  frame", "about which point", "do not invent variables", "coherent notation",
  "standard notation". For a whole paper rewrite, use mn-paper-rewrite and
  apply this notation inside it.
---

# Robotics notation

On every symbol the reader sees which axes it is written in and which point it refers to. The reader never meets a letter that only hides an expression. One page, one meaning per letter.

Worked example: `~/b2_ws/docs/z1/contact-wrench-math.md` (Z1 arm, Bota sensor, momentum observer, contact particle filter).

## Rules

1. **No placeholder letters.** Do not name an intermediate to shorten the algebra. Bad examples: `A = J^T`, `P` or `N` (projection), `G` (Gram matrix), `T` (transport), `ρ`, `e_r`, `F_r` (rotated coordinates). Write the real expression, or put a standard operator on it: $(J^\top)^{+}$, $[v]_\times$, $J^{-\top}$, $R^\top v$. A new letter is allowed only for a physical quantity (a length, a mass, a measured signal) or for a value that the code publishes.
2. **Frame on the left, point on the right** (Craig, *Introduction to Robotics*). ${}^{A}M_P$ is the moment about point $P$, written in the axes of $\{A\}$. Rotated coordinates are the same vector in other axes, ${}^{1}p_P$, never a new letter.
3. **One meaning per letter** on the whole page, across sections. Check the watchlist below before you choose a letter.
4. **Labels match like units.** In $J_{v,P}^\top F$ both terms are in one frame. In $J_{\omega,P}^\top M_P$ both refer to point $P$. Say this rule in the doc, so the reader can catch a mismatch.
5. **Joint-space vectors carry no labels.** $q$, $\dot q$ and $\tau$ have no frame and no point. Name variants with a text subscript of one family: $\tau_\text{ext}$, $\tau_\text{mob}$, $\tau_\text{err}$, $\tau_\text{res}$. Pick a joint with a second subscript: $\tau_{\text{ext},4}$.
6. **Say what a condition means physically.** After ${}^{W}M_C = 0$, write "the line of action of the force passes through $C$". After a zero Jacobian column, write which point lies on which axis.
7. **A unit never sits next to a formula.** Put units in table headers, or inside the math as `\ \mathrm{N}`. Never write "$(J^\top)^{+} f$ = (…) N": the N reads as part of the formula.
8. **Use model numbers, not letters, for a constant used once.** Write the MJCF offset `(0.218, 0, 0.057)` in the chain. Define a letter only for a distance that recurs and has a meaning, such as $\ell$ for the joint 5 axis to the tool point.
9. **The notation table comes first.** Frames, points, symbol patterns, joint-space vectors, other symbols. Each row gives the shape, the unit and the meaning.
10. **Give shapes at each map:** $(6\times3)(3) = 6$.

## Symbol patterns

| Pattern | Meaning |
|---|---|
| $\{A\}$ | a frame: $\{W\}$ world, $\{1\}\ldots\{6\}$ links, $\{B\}$ sensor, $\{G\}$ gripper |
| $C$, $B$, $O_i$, $P$, $Q$ | points, by capital letter. The origin of frame $\{B\}$ is point $B$. $O_i$ is the origin of link $i$, on the axis of joint $i$. $P$ and $Q$ are any points in a general rule. |
| ${}^{A}v$ | vector $v$ in the axes of $\{A\}$ |
| ${}^{A}p_P$ | position of $P$ from the origin of $\{A\}$, in $\{A\}$ axes |
| ${}^{A}(p_Q - p_P)$ | vector from $P$ to $Q$. It depends on the axes only. |
| ${}^{A}F$ | force. A force has no reference point. |
| ${}^{A}M_P$ | moment about $P$ |
| ${}^{A}w_P = ({}^{A}F, {}^{A}M_P)$ | wrench about $P$ |
| ${}^{A}R_B$ | orientation of $\{B\}$ in $\{A\}$: ${}^{A}v = {}^{A}R_B\,{}^{B}v$ |
| ${}^{A}a_i$ | unit direction of the axis of joint $i$ |
| ${}^{A}J_{v,P}$, ${}^{A}J_{\omega,P}$, ${}^{A}J_P$ | linear Jacobian of point $P$, angular Jacobian of the body that carries $P$, and the two stacked |
| ${}^{A}M_{P,x}$ | x component of ${}^{A}M_P$ |
| $\hat F$ | an estimate |
| $X^{+}$, $\sigma_k(X)$ | pseudo-inverse, and singular value $k$ of the matrix $X$ |

A frame label in front of a bracket applies to every vector inside it: ${}^{W}(a_i \times (p_C - p_{O_i}))$.

## Standard letters

| Quantity | Letter | Why |
|---|---|---|
| joint-space mass matrix | $H(q)$ | Featherstone. Keeps $M$ for the moment. |
| Coriolis matrix, gravity torque | $C(q, \dot q)$, $g(q)$ | Siciliano |
| gravity acceleration | ${}^{W}g_0$ | Siciliano. The vector differs from the torque $g(q)$. |
| joint axis direction | $a_i$ | not $z_i$, which clashes with the z component |
| linear and angular Jacobian | $J_v$, $J_\omega$ | not $J_p$, which clashes with a point named $p$ |
| cos and sin | $c_i$, $s_i$, $c_{234}$ | standard shorthand. Then no other $c$ or $s$ on the page. |
| a chi-square statistic or misfit | $\chi^2_\text{det}$, $\chi^2_j$ | the name says what it is |

## Collision watchlist

Letters that a robotics page tends to use twice:

- $M$: moment and mass matrix. Use $H(q)$ for the mass matrix.
- $L$: a length and a Cholesky factor. Write $\Sigma^{-1/2}$ for whitening.
- $r$: the observer residual and a lever arm. Write the lever as $p_P - p_{O_i}$.
- $p$: a point, the momentum and a probability. Write $H(q)\dot q$ in full, and give a share in words.
- $C$: Coriolis, a cone matrix and a contact point. Write cone edges as ${}^{W}d_{j,m}$.
- $S$: the sensor frame and a covariance. Name the sensor frame by its device, such as $\{B\}$.
- $w$: a wrench and filter weights. Use $\pi_j$ for weights, and then write angles in degrees.
- $\beta$, $\sigma$, $d$, $f$, $T$: check each one before reuse.
- N: the unit newton. Never use it as a symbol.

## Steps to rewrite a doc

1. **List the symbols.** Write every letter with each of its meanings, and mark the ones with two meanings or with no physical meaning.
2. **Name the frames and points.** Choose capital letters for the points and braces for the frames. Fill the notation section first.
3. **Rewrite section by section.** Replace each placeholder with its expression. Put a frame and a point on every vector.
4. **Sweep.** Search the file with `rg` for the old letters. The result must be empty.
5. **Recompute the numbers.** A notation change must not change a value. Rerun the source (such as `mj_jac` and numpy), and test each closed form against it at random poses.
6. **Check the math syntax.** Every `{` has its `}` and every `\begin` its `\end`. When node is present, parse with KaTeX.

## GitHub math

- Left superscript: `{}^{W}F`. Norm: `\lVert x \rVert`, never `|` inside a table.
- A `|` in a table cell outside math is `\|`.
- No `\,` inside `\text{}`. Write `N·m`. Use `45^\circ`, not `45°`, in math.
- End a display block, then start the next sentence on its own paragraph.
