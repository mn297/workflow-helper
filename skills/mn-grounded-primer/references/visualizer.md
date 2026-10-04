# Course visualizer (wave 5)

One page, one instrument per chapter. The reader moves a slider and sees the
chapter's object move and its numbers change. At the default settings every
readout shows the same numbers as the chapter text.

Reference instance: `/home/john/practice_kinematics/tutorial-lie-algebra/viz/lie-instruments.html`.
It has 12 stations and 46 node checks. The published copy is
https://claude.ai/artifact/1m5GeQmF5JgPczKXFECJAh.

## Steps

1. Collect the worked examples. For each chapter, read the docstring and the
   asserts of `exercises/exNN_*.py`. Write down the inputs and the numbers the
   script asserts. These become the instrument's default settings and the
   node checks. Completion: every chapter has its inputs and expected numbers.
2. Design one instrument per chapter. Each one shows the chapter's object
   doing the thing the chapter derives. Use one of three forms:
   - a 3D scene (frames, paths, a sphere or ball, a vector field),
   - a 3D scene plus a 2D plot (convergence, error against step size,
     angle against t),
   - a table station, for chapters about conventions or library differences.
   Give each station a lede of two to four sentences. Add a "Try this" line
   that names the setting where the point shows. Add an "In your code" list
   with the anchor `file:line` paths of the chapter's section 4, as written.
3. Write the maths as pure functions in one block between `/*MATH-START*/`
   and `/*MATH-END*/`, one `calcNN(...)` per chapter, in the forms of the
   README Notation section. The UI calls only these functions.
4. Run the node check. Extract the block, assert every chapter's numbers at
   its default inputs, and run `node --check` on the whole inline script.
   Completion: every assertion passes.
5. Render the page only in an isolated headless Chrome with CPU rendering.
   Never open a WebGL page in the user's own Chrome or a browser pane. On
   this machine, WebGL on the AMD iGPU crashed the whole desktop. Start
   Chrome with a profile in the session scratchpad:
   `/opt/google/chrome/chrome --headless=new --ozone-platform=headless --use-angle=swiftshader --enable-unsafe-swiftshader --remote-debugging-port=9333 --user-data-dir=<scratchpad>/profile`.
   Then drive it with
   `BU_NAME=sw BU_CDP_URL=http://127.0.0.1:9333 browser-harness`. At the
   end, stop that Chrome. Completion: every station renders with no console
   error.
6. Publish with the Artifact tool. Copy the same file to
   `<folder>/viz/<name>.html`. In the primer `README.md`, name both places.
   Say that the page loads three.js from a CDN. Say that the link is private
   until the user shares it.

## Mechanics that worked

- three.js r128 from `cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
  and `OrbitControls` from
  `cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`.
- One renderer and one canvas. Switching station disposes the old scene
  group and builds the new one. `camera.up` is z, to match robotics frames.
- Draw a frame as three cylinder-and-cone meshes under one 4x4 matrix. A
  matrix that is not a rotation (explicit Euler, elementwise lerp) then shows
  its skew and stretch.
- Plots on a 2D canvas, colors read from the CSS tokens with
  `getComputedStyle`. If the theme changes, rebuild the station. The 3D
  colors then follow.
- Keep control values in one map keyed by control id. A rebuild then keeps
  the user's settings.
- Play buttons keep a float accumulator and snap only the shown value.
  Slider labels print the value the maths uses.
- Deep links with a bare hash token, `#s01` to `#s12`.
