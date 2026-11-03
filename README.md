# g1lab

Drive and read a Unitree G1 humanoid from your own Python program: its two
arms and two hands by joint angles, its joints, tilt, hand pads,
temperatures and head camera. The robot keeps its own balance; your program
never touches the legs.

`g1lab` is the student package of the G1 Lab (Department of Mechanical
Engineering, The University of Iowa). The same program runs three ways:

- **on your laptop, with no robot:** `g1lab.mock()` runs the robot's own
  safety rules and a 3-D view, so a pose the robot would refuse is refused
  here too;
- **on the simulated robot** in the lab;
- **on the real robot** in the lab, without changes.

## Install

Python 3.8 or newer. Run this anywhere with internet (the lab's Robot
Network has none):

```
pip install "g1lab[camera,mock] @ https://github.com/rstory1/g1lab/releases/download/v0.1.1/g1lab-0.1.1-py3-none-any.whl"
```

`camera` adds Pillow (camera pictures as arrays), `mock` adds MuJoCo (the
laptop robot). Leave out what you do not need: `pip install "g1lab @ ..."`
is enough to drive the robot in the lab. The install with `camera` and
`mock` is about 240 MB, 30 MB of it `g1lab` itself (mostly the robot model
the mock uses).

**OpenCV is optional.** Add `video` (`g1lab[camera,mock,video]`, about
190 MB more) to show the camera in a live window and to write video files
(`examples/record_camera.py --video`). Without it everything else works:
driving the robot, reading the sensors, pictures as arrays, and recording
a dataset of pictures.

In the lab, the same file is also on the lab board,
`http://192.168.123.222:8090/`.

## A first program

```python
import math
import time
import g1lab

r = g1lab.mock()                                   # in the lab: g1lab.connect("192.168.123.222", name="ana")
home = r.info().home                               # the robot's standing pose

arm = home["right_arm"].copy()
arm[0] = math.radians(-60)                         # shoulder_pitch: raise the arm forward
arm[3] = math.radians(20)                          # elbow

with r.control() as c:                             # waits for your turn
    c.arms.move_to(right=arm, duration=2.0)        # smoothly, over 2 s
    c.hands.close("right")
    time.sleep(5)                                  # the arm stays up: g1lab keeps sending
# leaving the block lets go: the arms go home
```

## What is here

| | |
|---|---|
| [docs/camera_quickstart.md](docs/camera_quickstart.md) | watch the head camera, save pictures, record a dataset |
| [examples/](examples/) | small programs: `info.py`, `wave.py`, `raise_arm.py`, `sensors.py`, `record_camera.py`; each runs with `--host mock` |

```
python examples/wave.py --host mock --name ana
```

## Licence

`g1lab` is under the Apache License 2.0 ([LICENSE](LICENSE)). The wheel
also carries the Unitree G1 robot model and meshes, under their own terms:
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

This repository is written out from the lab's own code for each release
(version 0.1.1); changes are made there, not here.
