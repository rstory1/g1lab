# g1lab

Drive and read a Unitree G1 humanoid from your own Python program: its arms and
hands by joint angles, and its joints, tilt, hand pads, temperatures, camera,
depth and lidar; walk it to a point on a map, plan an arm reach and run missions in
the walking simulator. The robot keeps its own balance; your program never drives the
legs' joints.

Your program runs on the lab workstation, where you log in with your university ID. It
drives the simulated robot in the lab and, unchanged, the real robot once it opens.
`g1lab` is the student package of the G1 Lab (Department of Mechanical Engineering,
The University of Iowa).

## Install

Python 3.8 or newer. Install g1lab into your own account on the lab workstation, in a
virtual environment:

```
python3 -m venv ~/g1lab-env && . ~/g1lab-env/bin/activate
pip install "g1lab[camera,missions] @ https://github.com/rstory1/g1lab/releases/download/v0.1.20/g1lab-0.1.20-py3-none-any.whl"
```

`camera` adds Pillow (camera pictures as arrays) and `missions` adds PyYAML (mission
files); leave out what you do not need. Add `video` for OpenCV's live window and video
files, about 190 MB more, and `export` for turning recordings into a training set. Every
extra and what needs it:
[docs/guide.md](docs/guide.md#install).

To update, once installed:
`pip install http://192.168.123.222:8090/g1lab-0.1.20-py3-none-any.whl`

Check you are ready: `python -m g1lab.check`. Each
line says ok, note or FAIL, with the fix: your Python and packages, your address,
whether the lab board serves the same g1lab as yours, the robot computer's ports 5600 and
5601, and whether the robot is on and which features are. It only reads; nothing moves.

## A first program

```python
import math
import time
import g1lab

r = g1lab.connect()                            # the lab workstation, as the account you are logged in with
r.services.start("sim", wait=120)                      # the simulated robot; about 30 s the first time
print(r.info().features)                           # what is on now, and what turns the rest on
home = r.info().home                               # the robot's standing pose

arm = home["right_arm"].copy()
arm[0] = math.radians(-60)                         # shoulder_pitch: raise the arm forward
arm[3] = math.radians(20)                          # elbow

with r.control() as c:                             # waits until nobody else is moving the robot
    c.arms.move_to(right=arm, duration=2.0)        # smoothly, over 2 s
    c.hands.close("right")
    time.sleep(5)                                  # the arm stays up: g1lab keeps sending
# leaving the block lets go: the arms go home
r.close()
```

## What you can call

`help()` on any of these says more. Reading works any time, also while another program moves the robot.

| Read | Gives |
|---|---|
| `r.state.joints()` | `.q`, `.target`, `.temp` of all 29 joints; `.arm("right")`; `js["R_elbow"]` |
| `r.state.imu()` | body tilt: `.rpy` (rad), `.quat` |
| `r.state.temps()` | `["hottest"]["c"]` (with `["hottest"]["where"]`), `["body"]`, `["hand_r"]`, `["hand_l"]` (deg C) |
| `r.hands.state("right")` | `.q`, `.pads` (touch, named by `.pad_names`; `None` in the simulator), `.temp` |
| `r.camera.read()`, `r.camera.jpeg()` | `(t, picture)` as an RGB array or JPEG bytes |
| `r.depth.read()` | `(t, xyz, rgb)` 3-D points from the camera; robot only |
| `r.lidar.read()` | `.points()`: the lidar's points. The walking simulator gives a flat scan; the robot's 3-D lidar is not switched on yet |
| `r.lidar.imu()` | `.stamp`, `.gyro`, `.acc`: the lidar's own IMU; not switched on yet |
| `r.state.tf()` | where the lidar and camera sit on the body; not switched on yet |
| `r.on("joints", f)` | calls `f(value)` on each new reading; returns a function that stops it |
| `r.info()` | `.robot` (`"off"`, `"sim"` or `"robot"`), `.features` (each with `.on` and `.why`), `.home`, `.limits`, `.groups`, `.owner`, `.time_left` |
| `r.health()` | which feeds are live |

| Move, inside `with r.control() as c:` | Does |
|---|---|
| `c.arms.move_to(left=, right=, duration=2.0)` | go to 7 joint angles (rad) smoothly; returns when there |
| `c.arms.set(left=, right=)` | new target now, for your own control loop; returns at once |
| `c.arms.home()` | both arms to the standing pose |
| `c.hands.open("right")`, `c.hands.close("right", amount=1.0)` | open or make a fist; `"left"`, `"right"` or `"both"` |
| `c.hands.set("right", q)` | 7 hand joint angles (rad) |
| `c.status` | the robot's last answer: `.clamped`, `.held`, `.resting`, `.refused` |

An arm is 7 angles in this order: shoulder pitch, roll, yaw, elbow, wrist roll,
pitch, yaw. Errors you can catch: `g1lab.Refused` (that pose is not allowed),
`Busy` (someone else has the robot), `Off` (the robot is off, or the feature the call
needs is off; `err.feature` names it), `NoData` (that sensor is not sending),
`Disconnected`, `Ended` (the robot was turned off, or your control of it ended).

`r.services.start("sim")` turns the arm simulator on; a program that moves the arms needs
it, or the real robot. Walking needs the walking simulator, `r.services.start("walk")`.
`print(r.info().features)` says what is on now and, for each feature that is off, what
turns it on.

`r.ask("your question")` returns the language model's answer as text; it runs on the
robot computer and is refused while the real robot runs. The first question can take a
minute.

## Record a dataset

Saves the sensors to a folder and reads them back on one clock, so each camera picture
pairs with the right joints. It only listens, so it needs no hold on the robot and the robot does
not move. About 1.5 MB a second without depth.

```python
import g1lab

with g1lab.connect() as r:
    rec = g1lab.Recorder(r, "run1").run(60)        # 60 s

print(rec)                                         # what it got, and any gaps
for t, picture in rec.read("camera"):
    joints = rec.at("joints", t)                   # the joints at that moment
```

Or with no program: `python -m g1lab.record --host 192.168.123.222 --seconds 60 --out run1`
Add `--depth` for depth, and
`python -m g1lab.record show run1` to see what is in a recording.

Recordings become a LeRobot training set, one folder per demo, with your own rule
for which demos worked (add `export` to the extras in the install line):

```
python -m g1lab.export run1 run2 run3 --out pick --task "pick up the cube" --success mine.py
```

[docs/guide.md](docs/guide.md#turning-recordings-into-a-training-set) says what goes in `mine.py`.

## Walk, reach and run missions

In the lab these run in the walking simulator, which your program starts with
`r.services.start("walk")`; not on the real robot yet.

```python
import g1lab

r = g1lab.connect()
r.services.start("walk", wait=300)               # about a minute to start; the arms are yours too
p = r.nav.pose()                                 # x, y (m), yaw (rad) on the map
with r.control() as c:
    h = r.nav.go_to(p.x + 1.0, p.y, yaw=0.0)     # plan a route and walk it
print(h.result, h.reason)                        # "arrived", or why not
r.close()
```

`g1lab.reach` plans the right arm onto a point (`Unreachable` says why it cannot), and
`g1lab.mission` runs skills in a row from Python or a YAML file; in the walking simulator
the `go_to` and `home` steps run, and the ones that need a detector wait for one. Every result, every
error and the safety rules: [docs/walk_reach_missions.md](docs/walk_reach_missions.md).

## More

- [docs/guide.md](docs/guide.md): every call, what each error means, the
  language model, recording.
- [docs/joints_and_messages.md](docs/joints_and_messages.md): which way each joint
  turns, what the robot does to keep everyone safe, and the plain messages under `g1lab`.
- [docs/policy.md](docs/policy.md): your own network or class driving the arms and
  hands 50 times a second, sent from your program and trialled in the simulator; the operator approves it and runs it with you.
- [docs/walk_reach_missions.md](docs/walk_reach_missions.md): walking to a point, the arm
  reach solver, missions, and carrying while walking; [docs/missions.md](docs/missions.md):
  every skill and what each failure means.
- [docs/camera_quickstart.md](docs/camera_quickstart.md): camera pictures, depth, and
  how a pixel lines up with a 3-D point.
- [notebooks/](notebooks/): worked modules that show how to use each feature: joints and
  kinematics, trajectories, the camera and depth, recording a dataset, services and the
  language model, and handling refusals and errors.
- [examples/](examples/): `info.py`, `wave.py`, `raise_arm.py`, `sensors.py`,
  `record_camera.py`, `record_dataset.py`, `zed_easy.py` (the ZED's depth image, objects,
  people and pose), `zed_sdk.py` (the ZED SDK yourself, see
  [docs/zed_sdk_direct.md](docs/zed_sdk_direct.md)), `go_to_basic.py`,
  `reach_basic.py` and `carry_while_walking.py`. Each connects to the lab workstation;
  `--host` points it elsewhere: `python examples/wave.py --host ADDRESS`
- What changed in each release: [CHANGELOG.md](CHANGELOG.md).

## Licence

`g1lab` is under the Apache License 2.0 ([LICENSE](LICENSE)). The `notebooks/` folder also
holds Unitree's G1 robot description file, under its own terms: see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
