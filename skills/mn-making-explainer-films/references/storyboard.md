# The storyboard of a film, with a worked example

The example below is invented. It is a two-minute film on how a webcam's frames become the swing
angle of a pendulum. A Kalman filter estimates the angle: it predicts the next angle from the last
one, then corrects it with each frame's measurement. An encoder on the pivot gives the true angle;
the filter sees only the frames. The scenes and numbers are made up, but the shape and the density
are those of a real film. Use it as the model for the arc, the density of a scene, and the
captions. If `~/.config/skills/mn-making-explainer-films.local.md` exists, it names a real film on
this machine; read that one too.

## The arc

Ten scenes, each one claim and one picture, 5 to 24 seconds. The order follows the data, not the
code: the viewer should be able to say at every scene where the numbers on the stage came from.

| # | Scene | Seconds | The claim | The picture | The data on the stage |
|---|---|---|---|---|---|
| 0 | Title | 5 | the question in one line | the run's first picture, dimmed | run folder, commit |
| 1 | The ask | 12 | what we want out, thirty times a second | the webcam's own image, the true angle drawn over it, a loupe on the bob | the true angle per frame |
| 2 | Pictures | 13 | where the pictures and the truth come from (the one schematic) | a side view to scale: the camera, the rig, the lamp, the encoder on the pivot; the raw and the masked thumbnails | the camera pose, the rod length |
| 3 | Inputs | 11 | what the method gets, and nothing else | four cards: image, mask, the model, the first guess | the frame-0 image and mask, the model at two angles |
| 4 | Initialize | 13 | how the first fit finds the angle | mask pixels, the model rod sweeping onto them, a search readout counting down | the mask pixels, the start and the fitted angle, the log's error per search step |
| 5 | Track | 12 | points followed from frame to frame, blind to the object | real dots moving over real frames, trails, an alive counter | 87 of 120 tracks |
| 6 | Label | 14 | which part of the model each point is on | four worked examples with labels, then every dot colored by part, a legend with counts | the part labels of the run (rod, bob, background) |
| 7 | One frame | 24 | predict, measure, update: one step traced | the residual arrows (exaggerated, and said so), the predicted and the corrected angle, the uncertainty band narrowing, the gain as a bar | the measurements and residuals of one frame |
| 8 | The run | 16 | the estimate against the truth over all frames | truth and estimate over the frames, a loupe, a live error plot with phase bands (release, swing, rest) | the per-frame error |
| 9 | Numbers | 12 | what it reaches, what is missing | three big numbers, a short list of gaps, where the code and the equations are | `<metrics file>`, `<filter log>` |

## What each scene is made of

- One claim, stated in the first caption; the later captions of the scene add the number and the
  catch. One to three sentences each; they live in HTML under the stage, never inside the SVG.
- One picture, built once (`build`) and moved per frame (`render`). Labels on the stage are short:
  a name, a number with its unit, a frame counter.
- Real data: the pixel positions, the counts, the milliseconds, the RMS come from the run's files,
  extracted by a script kept beside the page. A drawn exaggeration says so on the stage and in the
  caption ("drawn sixteen times their size").
- A loupe when the motion is small in the picture: a nested `<svg>` whose `viewBox` follows the
  part of interest, showing the same picture and lines four times larger.
- A readout chip in a corner: frame, phase, the number of the scene.
- One color per kind of data for the whole film, taken from the project's own viewer when it has
  one (truth white, estimate cyan, measurement yellow, rejected red, accepted green).

## The data script

One Python script, run in the project's environment, writes one JSON: the images as small JPEG
data URIs (six frames at 960 x 540 and quality 70 are 60 to 90 KB each), the series and the
point lists rounded to 0.1 px, a sample of the tracks (a hundred, by class), one frame's residuals,
the per-frame error, the numbers from the log. A typical film's JSON is under 1 MB; the page limit
is 16 MB. Project 3D data into the camera's own image so that the overlays sit on the real picture.
