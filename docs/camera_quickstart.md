# The robot's camera: see it, save pictures, record

The robot has a camera in its head (a ZED 2i). You can watch it and save its
pictures from your own laptop. **None of this moves the robot, and you do not
need a session or a turn:** anyone on the Robot Network can read the camera at
the same time.

## 1. Get on the Robot Network and watch the camera

The Robot Network is a VLAN on the lab's network switch (addresses
`192.168.123.x`), with no internet. Your laptop has to be on it. Open
**http://192.168.123.222:8090/** in a browser: that page is the **lab
board**, and it shows what the camera sees, about 5 pictures a second. If
the page does not open, your laptop is not on the Robot Network. When it
says **No picture from the camera**, the camera is not sending, and your
program will get `NoData` too.

## 2. Install `g1lab`

The Robot Network has no internet, so install somewhere that has it:

```
pip install "g1lab[camera] @ https://github.com/rstory1/g1lab/releases/download/v0.1.1/g1lab-0.1.1-py3-none-any.whl"
```

In the lab, `g1lab` is also on the lab board:
`pip install http://192.168.123.222:8090/g1lab-0.1.1-py3-none-any.whl`.

You need Python 3.8 or newer.

For the live window (section 4) and video files (section 5) you also need
OpenCV. It is optional because it is large (about 190 MB); to install it
with `g1lab`, use this line instead:

```
pip install "g1lab[camera,video] @ https://github.com/rstory1/g1lab/releases/download/v0.1.1/g1lab-0.1.1-py3-none-any.whl"
```

Without it, everything else here works: watching on the lab board, saving
pictures, pictures as arrays and recording a dataset of pictures.

## 3. Save one picture

```python
import g1lab

r = g1lab.connect("192.168.123.222", name="ana")   # use your own name
t, jpeg = r.camera.jpeg()                          # the newest picture, as a JPEG file
open("view.jpg", "wb").write(jpeg)

t, img = r.camera.read()                           # the same, as a numpy array
print(img.shape)                                   # (480, 640, 3), colours in RGB order
r.close()
```

## 4. A live window

Needs OpenCV (section 2).

```python
import cv2
import g1lab

r = g1lab.connect("192.168.123.222", name="ana")
while True:
    t, img = r.camera.read()
    cv2.imshow("robot camera", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))   # OpenCV wants BGR
    if cv2.waitKey(1) == ord("q"):                                     # q to quit
        break
r.close()
```

Put your detector between `read()` and `imshow()`.

## 5. Record pictures for a dataset

Save this as `record_camera.py`:

```python
import csv, os, sys, time
import g1lab

out = sys.argv[1] if len(sys.argv) > 1 else "pictures"
seconds, per_second = 30, 2                      # change these
video = False                                    # True also writes video.mp4 (needs OpenCV, section 2)
r = g1lab.connect("192.168.123.222", name="ana")
os.makedirs(out, exist_ok=True)
writer = None
with open(os.path.join(out, "frames.csv"), "w", newline="") as fh:
    log = csv.writer(fh)
    log.writerow(["frame", "camera_time"])
    n, last, end = 0, None, time.time() + seconds
    while time.time() < end:
        t, jpeg = r.camera.jpeg()
        if t == last:                            # the same picture again
            time.sleep(0.01)
            continue
        last, n = t, n + 1
        open(os.path.join(out, f"frame_{n:05d}.jpg"), "wb").write(jpeg)
        log.writerow([n, t])
        if video:
            import cv2
            t, img = r.camera.read()
            if writer is None:
                writer = cv2.VideoWriter(os.path.join(out, "video.mp4"),
                                         cv2.VideoWriter_fourcc(*"mp4v"), per_second, (640, 480))
            writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        time.sleep(1 / per_second)
if writer is not None:
    writer.release()
r.close()
print("saved", n, "pictures in", out)
```

Run it: `python3 record_camera.py mugs`. Move the object between pictures:
different sides, distances, lighting and backgrounds make a better dataset
than many pictures of one view. For smooth video, set `per_second = 15`
(every picture the camera sends).

## 6. Depth: what the camera sees in 3-D

**Depth is already running on the robot.** The robot's own computer
works out depth from both camera eyes and sends it out as 3-D points, 5
times a second. You do not need to compute anything or install anything
more: like the pictures, it needs no session or turn, and anyone on the
Robot Network can read it.

```python
import numpy as np
import g1lab

r = g1lab.connect("192.168.123.222", name="ana")   # use your own name
t, xyz, rgb = r.depth.read()                       # the newest points
print(len(xyz), "points")                          # up to 20000

ahead = xyz[np.abs(xyz[:, 1]) < 0.2]               # a strip 0.4 m wide, straight ahead
if len(ahead):
    print("nearest thing ahead:", ahead[:, 0].min().round(2), "m")

np.savez("depth.npz", t=t, xyz=xyz, rgb=rgb)       # keep it for later
```

- **`xyz`** is one row per point, in metres, from the camera's left eye:
  **x forward, y to the robot's left, z up**. The camera moves with the
  head, so these are not room coordinates.
- **`rgb`** is each point's colour (0 to 255), row for row with `xyz`.
- **`t`** is when the camera took it, by the robot's clock, like the
  pictures' `t`.
- Only points the camera could measure are there: from about 0.3 m
  (1 ft) out to 10 m (33 ft), on surfaces with some texture. Plain walls,
  shiny things and anything nearer than 0.3 m can be missing.
- To get every new set as it arrives instead of asking, use
  `r.on("depth", f)`: it calls `f((t, xyz, rgb))` each time.
- Depth comes only from the robot: `g1lab.mock()` has none (`r.depth.read()`
  there raises `NoData`).

## What the pictures are

- **640 × 480**, from the camera's **left eye**, corrected for lens
  distortion. The camera is wide (16:9); you get the 4:3 middle of it.
- **Up to 15 pictures a second.** The lab board shows fewer; your program gets
  all of them.
- **`t` is when the camera took the picture**, by the robot's own clock.
  That clock can be hours off from your laptop's, so use `t` to put pictures
  in order or measure time between them, not as the time of day.
- **Depth** is already computed on the robot: see section 6.
- **Both eyes at full size** are only for computing depth your own way. They
  come from the ZED SDK stream at `192.168.123.164:30000`, which only the ZED
  SDK can open, and the SDK needs an NVIDIA graphics card (the lab
  workstation has one; most laptops do not).

## Practise without the robot

`g1lab.mock()` instead of `g1lab.connect(...)` plays a short recorded clip of
the lab through `r.camera`, so the code above runs anywhere, with no
network. It needs MuJoCo, so install `g1lab` with it:

```
pip install "g1lab[camera,mock] @ https://github.com/rstory1/g1lab/releases/download/v0.1.1/g1lab-0.1.1-py3-none-any.whl"
```

`g1lab.mock(camera="render")` draws a simulated camera view with a red ball
instead.

## If something goes wrong

| What you see | What it means |
|---|---|
| The browser cannot open the lab board | Your laptop is not on the Robot Network |
| `NoData` after 2 seconds | The camera is not sending; the lab board says "No picture from the camera" |
| `ModuleNotFoundError: PIL` | `pip install pillow` (needed for `camera.read()`) |
| Colours look wrong in OpenCV | Convert RGB to BGR, as in section 4 |
