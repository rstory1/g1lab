# The robot's camera: see it, save pictures, record

The robot has a camera in its head (a ZED 2i). You can watch it and save its
pictures from your own laptop. **None of this moves the robot, and you do not
need a session or a turn:** anyone on the Robot Network can read the camera at
the same time.

## 1. Get on the Robot Network and watch the camera

The Robot Network is a VLAN on the lab's network switch, with no internet. Plug
your laptop into a Robot Network port on the switch and set the wired connection
by hand in your network settings:

| | |
|---|---|
| IP address | `192.168.123.N`, where N is 130 to 159 and nobody else in the lab is using it |
| Subnet mask | `255.255.255.0` |
| Router and DNS | leave empty, so your Wi-Fi keeps your internet |

Then open **http://192.168.123.222:8090/** in a browser: that page is the **lab
board**, and it shows what the camera sees, about 5 pictures a second. If
the page does not open, check the cable and those settings. When it
says **No picture from the camera**, the camera is not sending, and your
program will get `NoData` too.

## 2. Install `g1lab`

Python 3.8 or newer, somewhere with internet (the Robot Network has none):

```
pip install "g1lab[camera] @ https://github.com/rstory1/g1lab/releases/download/v0.1.3/g1lab-0.1.3-py3-none-any.whl"
```

The live window in section 4 also needs OpenCV (about 190 MB): use
`g1lab[camera,video]` in that line.

To update in the lab, once installed:
`pip install http://192.168.123.222:8090/g1lab-0.1.3-py3-none-any.whl`

## 3. Save one picture

```python
import g1lab

r = g1lab.connect("192.168.123.222", name="YOURNAME")  # use your own name
t, jpeg = r.camera.jpeg()                              # the newest picture, as a JPEG file
open("view.jpg", "wb").write(jpeg)

t, img = r.camera.read()                               # the same, as a numpy array
print(img.shape)                                       # (480, 640, 3), colours in RGB order
r.close()
```

## 4. A live window

Needs OpenCV (section 2).

```python
import cv2
import g1lab

r = g1lab.connect("192.168.123.222", name="YOURNAME")
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
r = g1lab.connect("192.168.123.222", name="YOURNAME")
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
more: like the pictures, it needs no session or turn, and anyone on the
Robot Network can read it.

```python
import numpy as np
import g1lab

r = g1lab.connect("192.168.123.222", name="YOURNAME")  # use your own name
t, xyz, rgb = r.depth.read()                           # the newest points
print(len(xyz), "points")                              # up to 20000

ahead = xyz[np.abs(xyz[:, 1]) < 0.2]                   # a strip 0.4 m wide, straight ahead
if len(ahead):
    print("nearest thing ahead:", ahead[:, 0].min().round(2), "m")

np.savez("depth.npz", t=t, xyz=xyz, rgb=rgb)           # keep it for later
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
- **Both eyes at full size** are only for computing depth your own way. They
  come from the ZED SDK stream at `192.168.123.164:30000`, which only the ZED
  SDK can open, and the SDK needs an NVIDIA graphics card (the lab
  workstation has one; most laptops do not).

## Which pixel is a 3-D point

The picture and the depth points share one lens, so you can put a depth point on
the picture, or find how far away something in the picture is. For the 640 × 480
picture, in pixels: focal length **352.1**, centre **325.3, 234.6**.

```python
import numpy as np
import g1lab

r = g1lab.connect("192.168.123.222", name="YOURNAME")
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

## Practise without the robot

`g1lab.mock()` instead of `g1lab.connect(...)` plays a short recorded clip of the
lab through `r.camera`, so the picture code above runs anywhere, with no network.
It needs MuJoCo: use `g1lab[camera,mock]` when you install. `g1lab.mock(camera="render")`
draws a simulated camera view with a red ball instead.

## If something goes wrong

| What you see | What it means |
|---|---|
| The browser cannot open the lab board | Your laptop is not on the Robot Network: see section 1 |
| `NoData` after 2 seconds | The camera is not sending; the lab board says "No picture from the camera" |
| `ModuleNotFoundError: PIL` | `pip install pillow` (needed for `camera.read()`) |
| Colours look wrong in OpenCV | Convert RGB to BGR, as in section 4 |
