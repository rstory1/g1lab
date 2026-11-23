# Your own detector: `r.vision`


Train a detector, export it to ONNX, and it runs on the robot's own computer. You get
what it found, with a 3-D point for each thing.

**Where it runs today.** On `g1lab.mock()`, now: the mock runs your model on your own
computer, through the robot's own checks, and needs the `vision` extra (onnxruntime;
[Install](guide.md#install)). Use `g1lab.mock(camera="render")`: it draws depth with each
picture, so detections get their 3-D point; with the recorded clip `xyz` is `None`. On the
robot it is not switched on yet, and `upload()` is refused with "the vision slot on the
robot's Jetson does not answer"; the same program will work there unchanged once it is.
The [Vision model module](../notebooks/vision_model.ipynb) goes through all of it.

```python
r.vision.upload("castings.onnx", "castings.json")   # checked first; raises if it fails
r.vision.activate("castings")                       # runs while this program runs

for d in r.vision.read():
    print(d.label, d.conf, d.box, d.xyz)            # d.xyz: metres, pelvis frame, or None
```

`castings.json`, the manifest:

```json
{"name": "castings", "task": "detect", "classes": ["casting", "bin"],
 "input": {"width": 640, "height": 640}}
```

| Field | What it says |
|---|---|
| `name` | up to 40 letters, digits, `-` and `_` |
| `task` | `detect`, `pose` or `segment` for the Ultralytics export layout; `raw` for anything else |
| `classes` | your class names, in the model's order |
| `input` | the size your model takes. `"resize": "stretch"` instead of the default letterbox; `"scale"`, what pixels are divided by (default 255) |
| `conf`, `iou` | optional; defaults 0.25 and 0.45 |
| `keypoints` | a pose model's keypoint names, in order |
| `post` | `true` if you send a post.py |
| `max_ms` | optional; refuse the model if it takes longer than this on a frame |

Export from Ultralytics with `model.export(format="onnx", imgsz=640)`, leaving `nms` off.
The upload loads the model, runs it on a test picture, measures it, and tells you what
is wrong if it fails. A model belongs to the `name=` your program connected
with: only that name can replace or remove it, so keep it the same between runs.

A `Detection` has `model`, `label`, `conf`, `box` (x1, y1, x2, y2 in camera pixels, 640 x 480),
`xyz` (x forward, y left, z up, in metres, from the pelvis), `xyz_cam` (the same from the camera)
and `n_depth` (how many depth points it rests on). `xyz` is `None` when the depth or the
joints did not say: check it before you use it. A pose model adds `keypoints` and
`keypoints_xyz`; a segmentation model adds `mask`, a boolean array.

**Several models.** Models stay on the robot until `r.vision.remove(name)`, and none runs until a
program activates it. Several can run at once, and `d.model` says which found what. They share each
camera frame's time: `activate()` raises `ServiceRefused`, with the numbers, when they would
not keep up. Training one model on all your classes is then the way to run them, because finished
ONNX files cannot be combined. `r.vision.deactivate(name)` lets go; a model also stops about 30 s
after your program ends.

**Another model layout: post.py.** A `raw` model hands its outputs to your script, which runs on the
robot beside the model. This one reads an output of `[n, 6]` rows, x1 y1 x2 y2 confidence class,
in the model's own pixels:

```python
def post(image, outputs, detections, manifest):
    h, w = image.shape[:2]
    sx, sy = w / manifest["input"]["width"], h / manifest["input"]["height"]
    return [{"box": [a * sx, b * sy, c * sx, d * sy], "conf": float(p), "cls": int(k)}
            for a, b, c, d, p, k in outputs[0] if p > 0.5]
```

```python
r.vision.upload("rfdetr.onnx", "rfdetr.json", post="post.py")    # "task": "raw", "post": true, "resize": "stretch"
```

`image` is the camera picture, RGB. For a `detect`, `pose` or `segment` model `detections` already
holds what was decoded, so a post.py can filter or add to it; anything small in a detection's `extra`
reaches your program. The script has numpy and no network, and sees none of the robot's files. If it raises,
the model stops and `r.vision.models()` says why in `stopped`; what it prints goes to a log on the robot.

**On the mock, three things differ.** Your model runs in your own program, not a sandbox, so
what a post.py prints shows in your output. Its time per frame is your computer's, and the
robot's limit (100 ms a frame for all running models together) is not applied: the robot
measures the model again when you upload it there. Models last as long as the mock.
