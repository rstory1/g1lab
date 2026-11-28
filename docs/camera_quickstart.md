# The robot's camera: see it, save pictures, record

The robot has a camera in its head (a ZED 2i). You can watch it and save its
pictures from your own program on the lab workstation. **None of this moves the
robot, and you do not need to hold the robot:** every program can read the
camera at the same time.

## 1. Watch the camera

Logged in on the lab workstation, open **http://192.168.123.222:8090/** in its
browser: that page is the **lab board**, and it shows what the camera sees, about 5
pictures a second. When it says **No picture from the camera**, the camera is not
sending, and your program will get `NoData` too.

## 2. Install `g1lab`

Python 3.8 or newer, in your own account on the lab workstation, in the virtual
environment the Install section of the README sets up:

```
pip install "g1lab[camera] @ https://github.com/rstory1/g1lab/releases/download/v0.1.20/g1lab-0.1.20-py3-none-any.whl"
```

The live window in section 4 also needs OpenCV (about 190 MB): use
`g1lab[camera,video]` in that line.

To update, once installed:
`pip install http://192.168.123.222:8090/g1lab-0.1.20-py3-none-any.whl`

Then `python -m g1lab.check`: one line per check with the fix, from your address to
whether the camera's stream (port 5601) reaches you. Nothing moves.

## 3. Save one picture

```python
import g1lab

r = g1lab.connect()
t, jpeg = r.camera.jpeg()                              # the newest picture, as a JPEG file
open("view.jpg", "wb").write(jpeg)

t, img = r.camera.read()                               # the same, as a numpy array
print(img.shape)                                       # (480, 640, 3), colors in RGB order
r.close()
```

## 4. A live window

Needs OpenCV (section 2).

```python
import cv2
import g1lab

r = g1lab.connect()
while True:
    t, img = r.camera.read()
    cv2.imshow("robot camera", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))   # OpenCV wants BGR
    if cv2.waitKey(1) == ord("q"):                                     # q to quit
        break
r.close()
```

Put your detector between `read()` and `imshow()`.

## 5. Save pictures for a dataset

```python
import os, time
import g1lab

os.makedirs("mugs", exist_ok=True)
r = g1lab.connect()
for n in range(60):                                    # 60 pictures, 2 a second
    t, jpeg = r.camera.jpeg()
    open(f"mugs/{n:03d}.jpg", "wb").write(jpeg)
    time.sleep(0.5)
r.close()
```

Move the object between pictures: different sides, distances, lighting and
backgrounds make a better dataset than many pictures of one view.

## 6. Depth: what the camera sees in 3-D

**Depth is already running on the robot.** The robot's own computer
works out depth from both camera eyes and sends it out as 3-D points, 5
times a second. You do not need to compute anything or install anything
more: like the pictures, it needs no hold on the robot, and every program on the
Robot Network can read it.

```python
import numpy as np
import g1lab

r = g1lab.connect()
t, xyz, rgb = r.depth.read()                           # the newest points
print(len(xyz), "points")                              # up to 20000

ahead = xyz[np.abs(xyz[:, 1]) < 0.2]                   # a strip 0.4 m wide, straight ahead
if len(ahead):
    print("nearest thing ahead:", ahead[:, 0].min().round(2), "m")

np.savez("depth.npz", t=t, xyz=xyz, rgb=rgb)           # keep it for later
```

- **`xyz`** is one row per point, in meters, from the camera's left eye:
  **x forward, y to the robot's left, z up**. The camera moves with the
  head, so these are not room coordinates.
- **`rgb`** is each point's color (0 to 255), row for row with `xyz`.
- **`t`** is when the camera took it, by the robot's clock, like the
  pictures' `t`.
- Only points the camera could measure are there: from about 0.3 m
  (1 ft) out to 10 m (33 ft), on surfaces with some texture. Plain walls,
  shiny things and anything nearer than 0.3 m can be missing.
- To get every new set as it arrives instead of asking, use
  `r.on("depth", f)`: it calls `f((t, xyz, rgb))` each time.
- Depth comes only from the real robot's camera; the simulator sends none.

## 7. Depth for every pixel, and the ZED's objects, bodies and pose

Section 6 gives you 3-D points. The ZED's own software can also give you
a **depth image** (a distance for every pixel of the picture) and can find
**things and people** in the picture and track **where the camera is**. These
take the robot computer's graphics card, so they are **off until you ask**:

```python
import numpy as np
import g1lab

r = g1lab.connect()
r.services.start("zed", wait=180)           # usually a few seconds, up to a minute the first time

t, depth = r.depth.image(timeout=60)        # float32, 480 x 640, meters; NaN where unmeasured
                                            # (the first one comes a few seconds after "running")
t, img = r.camera.read()                    # the same pixels: depth[v, u] is the distance at img[v, u]
print("center of the picture:", np.nanmedian(depth[230:250, 310:330]).round(2), "m")
print("measured:", round(100 * np.isfinite(depth).mean()), "% of pixels")

for o in r.zed.objects():                   # things the ZED recognizes
    print(o.label, o.confidence, "at", o.position.round(2), "m, box", o.bbox)

for body in r.zed.bodies():                 # people, with a skeleton
    print(body.id, "right wrist at", body.kp("r_wrist").round(2), "m")

print(r.zed.pose().position)                # where the camera is now
r.close()
```

**The example program.** `examples/zed_easy.py` does all of this and
prints what the ZED sees once a second:

```
python examples/zed_easy.py
python examples/zed_easy.py --seconds 30 --picture seen.jpg
```

`--picture` saves the camera picture with the boxes, the skeletons and a few
distances drawn on it (it needs Pillow, g1lab's `camera` option).

When you are done, `r.services.stop("zed")`; it also stops by itself 10
minutes after your program stops using it. The card is shared: if it is too
full `start` says so with the numbers.

- **The depth image lines up with the picture, pixel for pixel.** Both are
  640 x 480 and use the same lens numbers (focal length 352.1, center
  325.3, 234.6, as in [Which pixel is a 3-D point](#which-pixel-is-a-3-d-point) below), so `depth[v, u]` is the distance at
  `img[v, u]`. A pixel `(u, v)` at distance `d` is the point
  `x = d`, `y = d * (325.3 - u) / 352.1`, `z = d * (234.6 - v) / 352.1`
  (forward, left, up). Note that `d` is the distance straight out from the camera, not the
  distance along the pixel's ray.
- **`NaN` means no measurement** (too near, too shiny, too far, or hidden from
  one eye), not zero. Use `np.isfinite(depth)` or `np.nanmedian(...)`.
- **Up to 5 depth images a second.** They are about 200 to 300 KB each, so a
  program that only wants the 3-D points of section 6 does not receive them.
- **Objects** (`r.zed.objects()`): each has `id` (the same while the ZED
  keeps tracking it), `label` (PERSON, VEHICLE, BAG, ANIMAL, ELECTRONICS,
  FRUIT_VEGETABLE or SPORT), `confidence` (0 to 100), `position` and
  `velocity` (meters, in the camera's frame: forward, left, up), `dimensions`,
  and `bbox`, the box `(x0, y0, x1, y1)` **in the pixels of the 640 x 480 picture**
  (`None` when the thing is in a side strip the picture does not show). An empty
  list means the ZED sees nothing, not that it is off.
- **Bodies** (`r.zed.bodies()`): each person has 18 keypoints (the ZED's
  `BODY_18` skeleton: nose, neck, shoulders, elbows, wrists, hips, knees,
  ankles, eyes, ears). `keypoints` are 3-D points in meters, `keypoints_2d` are
  pixels of the picture, and `body.kp("r_wrist")` reads one by name. A joint the
  ZED cannot see is `NaN`, so check `np.isfinite`.
- **Pose** (`r.zed.pose()`): where the camera is, as `position` (meters) and
  `quat` (w, x, y, z), in a level frame set when the service started: z
  straight up, x the way the camera faced then, flattened, y left. The head
  camera looks down, so even at the start `quat` is not (1, 0, 0, 0): it
  holds that tilt. The service forgets the frame when it restarts. The camera moves with the
  robot's head, so this follows the head, not the room.
- Every one has a `t`, on the robot's clock like the pictures'. To get each
  one as it arrives, use `r.on("depth.image", f)`, `r.on("zed.objects", f)`,
  `r.on("zed.bodies", f)` or `r.on("zed.pose", f)`.
- With no data, each call raises `NoData` and says to start the service.

**Want the ZED SDK itself?** If you would rather call the ZED's own API (its
settings, its other detectors, your own depth mode), open the camera's stream
yourself: [zed_sdk_direct.md](zed_sdk_direct.md).

## What the pictures are

- **640 × 480**, from the camera's **left eye**, corrected for lens
  distortion. The camera is wide (16:9); you get the 4:3 middle of it.
- **Up to 15 pictures a second.** The lab board shows fewer; your program gets
  all of them.
- **`t` is when the camera took the picture**, by the robot's own clock.
  That clock can be off from the workstation's, so use `t` to put pictures
  in order or measure time between them, not as the time of day.
- **Both eyes at full size** are only for computing depth your own way. They
  come from the ZED SDK stream at `192.168.123.164:30000`, which only the ZED
  SDK can open, and the SDK needs an NVIDIA graphics card (the robot
  computer has one). Section 7 uses it for you; to use it
  yourself see [zed_sdk_direct.md](zed_sdk_direct.md).

## Which pixel is a 3-D point

The picture and the depth points share one lens, so you can put a depth point on
the picture, or find how far away something in the picture is. For the 640 × 480
picture, in pixels: focal length **352.1**, center **325.3, 234.6**.

```python
import numpy as np
import g1lab

r = g1lab.connect()
t, img = r.camera.read()
t, xyz, rgb = r.depth.read()
x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]              # forward, left, up, as in section 6

u = np.round(325.3 - 352.1 * y / x).astype(int)        # across, from the picture's left
v = np.round(234.6 - 352.1 * z / x).astype(int)        # down, from the picture's top

on_your_object = (abs(u - 320) < 20) & (abs(v - 240) < 20)      # the points in a box you found
if on_your_object.any():
    print("it is", np.median(x[on_your_object]).round(2), "m ahead")
r.close()
```

Going the other way, a pixel `(u, v)` looks along the direction
`(1, (325.3 - u) / 352.1, (234.6 - v) / 352.1)`: forward, left, up.

## If something goes wrong

| What you see | What it means |
|---|---|
| The browser cannot open the lab board | The gateway is not running, or the workstation is not on the Robot Network: `python -m g1lab.check` says which |
| `NoData` after 2 seconds | The camera is not sending; the lab board says "No picture from the camera" |
| `NoData` from `r.depth.image()` or `r.zed...` | The zed service is not running: `r.services.start("zed")` |
| `NoData` or `ServiceRefused` from the zed calls while a simulator runs | The ZED's data comes from the real camera only; in the simulator use `r.camera.read()` |
| `ServiceRefused` from `start("zed")` | The graphics card is too full right now; the message gives the numbers. Try again later |
| `r.camera.read() needs Pillow or OpenCV to decode the picture: pip install pillow ...` | Add `camera` to the extras in the install line (section 2): `camera.read()` needs it |
| Colors look wrong in OpenCV | Convert RGB to BGR, as in section 4 |
