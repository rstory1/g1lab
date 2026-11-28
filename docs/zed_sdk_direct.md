# Using the ZED SDK yourself

`g1lab` gives you the ZED's depth image, objects, bodies and pose
without installing anything ([camera_quickstart.md](camera_quickstart.md),
section 7). If you want more than that (the SDK's settings, its other
detectors, your own depth mode, your own tracking), use the ZED SDK
directly. Nothing blocks you: the robot's camera is open to the SDK.

## How it works

Only one program can open the camera itself, and that is the robot's own
camera server. It also **streams the camera, both eyes, over the network** at
`192.168.123.164`, port `30000`. Your program opens that stream as if it were
the camera. After that it is the normal ZED API, and the SDK samples work.

```python
import pyzed.sl as sl

init = sl.InitParameters()
init.set_from_stream("192.168.123.164", 30000)          # the robot's stream, not a USB camera
init.depth_mode = sl.DEPTH_MODE.NEURAL                   # computed here, on your graphics card
init.coordinate_units = sl.UNIT.METER
init.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP_X_FWD   # x forward, y left, z up

cam = sl.Camera()
if cam.open(init) != sl.ERROR_CODE.SUCCESS:
    raise SystemExit("cannot open the stream: is the robot on, and is its camera server running?")

image, depth = sl.Mat(), sl.Mat()
rt = sl.RuntimeParameters()
while cam.grab(rt) == sl.ERROR_CODE.SUCCESS:
    cam.retrieve_image(image, sl.VIEW.LEFT)
    cam.retrieve_measure(depth, sl.MEASURE.DEPTH)
    print(depth.get_data().shape)                        # 720 x 1280: the full frame, not the 640 x 480 crop
    break
cam.close()
```

## The example program

`examples/zed_sdk.py` is a complete program to start from. It opens the
stream as above, prints the distance straight ahead once a second, and with
`--objects` runs the SDK's object detection and puts each box on the 640 x 480
picture. It does not use `g1lab`.

```
PY=~/zedenv/bin/python                                # your Python with pyzed (see "Get pyzed" below)

$PY examples/zed_sdk.py                         # the robot's stream, 10 s
$PY examples/zed_sdk.py --objects --seconds 30 --picture seen.jpg
$PY examples/zed_sdk.py --svo episode.svo2 --objects   # a recording, no robot
```

The example uses
`NEURAL_LIGHT` depth unless you ask for another (`--depth-mode NEURAL`): the
lightest on a shared graphics card. `--picture` needs OpenCV. The first run
on a computer prepares each model it uses, which takes minutes.

## Match the robot's axes

Ask for `RIGHT_HANDED_Z_UP_X_FWD` and `METER`, as above. Then your numbers
agree with `g1lab`'s `r.depth.read()`: x forward, y left, z up, from the
camera. Two things differ from the 640 x 480 picture of `r.camera.read()`:

- The stream is the **full 16:9 frame** (1280 x 720). The picture is its
  4:3 middle, cut to 960 x 720 and shrunk to 640 x 480. To put your pixels on the picture,
  subtract 160 from x, then multiply both by 2/3.
- So the picture's focal length (352.1) is the stream's times 2/3. Read the
  stream's own numbers from `cam.get_camera_information()`.

## Where it can run

It needs an **NVIDIA graphics card** and the **ZED SDK**. The lab workstation has
both: the SDK (version 5.6) is installed for every account, so you only need pyzed in
your own Python (below). Nothing else to set: no `export` lines. The robot's camera
server runs SDK 5.0.7; SDK 5.6 opens its stream, with depth, objects, bodies and
tracking. The H.265 stream takes a few Mbit/s.

## Get pyzed

pyzed is the SDK's Python package. Stereolabs' script installs it into
whichever Python runs it, so make your own environment and run it from there.
The `pip` line and the script download files; the workstation has internet, so
they work as shown:

```
python3 -m venv ~/zedenv
~/zedenv/bin/pip install --upgrade pip numpy requests
~/zedenv/bin/python "$(find / -xdev -name get_python_api.py -not -path "$HOME/*" 2>/dev/null | head -1)"
~/zedenv/bin/python -c "import pyzed.sl as sl; print(sl.Camera.get_sdk_version())"
```

The `find` line locates the script the SDK installed. The last line prints the SDK version (5.6.0). For
`--picture`, also `~/zedenv/bin/pip install opencv-python`.

pyzed is built for one SDK version. When the SDK on a computer changes, a pyzed
installed before stops importing (`undefined symbol`): run the
`get_python_api.py` line again with the same Python.

## Rules

1. **Never open the camera itself.** Only the robot's camera server does. Open
   the stream, as above. A program that tries the camera directly gets nothing
   and can get in the way of the others.
2. **Your program computes its own depth, on the workstation's graphics card.**
   **It sits outside the graphics-card check:** that check keeps room for the robot's
   controller when you use `r.services.start(...)`, and it does not know your program
   is there. The robot's controller shares that card, so a neural depth running
   next to it can slow it. **If the operator asks you to stop, stop at once.**
   Prefer `NEURAL_LIGHT` while the robot is running, and close the camera
   (`cam.close()`) as soon as you are done.
3. **Read only.** The stream gives you pictures. It cannot move the robot. To
   move it, use `g1lab` as usual.
4. Several programs can open the stream at the same time, `g1lab`'s zed
   service among them. If the service is running and the card is busy, you
   will both be slower.

## Practice without the robot

An **SVO2 file** is the ZED SDK's own recording (both eyes and the IMU).
You can play one back with the same SDK, with no robot
and no stream: use `init.set_from_svo_file("episode.svo2")` instead of
`set_from_stream`. `examples/zed_sdk.py --svo` does this.

## If something goes wrong

| What you see | What it means |
|---|---|
| `open` fails with a connection error | The robot or its camera server is off. Open the lab board ([camera_quickstart.md](camera_quickstart.md) section 1): if it shows no picture, the camera is down |
| `import pyzed` fails with `undefined symbol` | Your pyzed was built for another SDK version. Rerun the `get_python_api.py` line in "Get pyzed" with your Python |
| The first `open` on a computer stops at `Looking for its calibration` | The SDK downloads the camera's calibration from Stereolabs the first time. The workstation already has the file, so this should not happen there |
| The first `open` seems to hang for minutes | The SDK is preparing the neural depth model for your card; it only does this the first time |
| `CAMERA NOT INITIALIZED` after it worked | The stream broke (the robot restarted): `cam.close()`, wait a second, and open again. An `open` straight after a `close` fails |
| `enable_positional_tracking` says `HIGH FREQUENCY SENSORS DATA REQUIRED` | The stream carries the IMU at the picture's rate only (30 Hz), too slow for the SDK's IMU fusion. Set `enable_imu_fusion = False` in `PositionalTrackingParameters`; tracking then runs from the pictures |
| The first object or body detection takes minutes to start | The SDK downloads and prepares each detection model for your card the first time (several minutes each); later starts take seconds |
| Depth in the wrong directions | You forgot `RIGHT_HANDED_Z_UP_X_FWD` |
