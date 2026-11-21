# g1lab

Drive and read a Unitree G1 humanoid from your own Python program: its arms and
hands by joint angles, and its joints, tilt, hand pads, temperatures, camera,
depth and lidar; walk it to a point on a map, plan an arm reach and run missions in
the walking simulator. The robot keeps its own balance; your program never drives the
legs' joints.

The same program runs on your laptop with no robot (`g1lab.mock()` refuses what
the robot refuses), on the simulated robot in the lab, and, unchanged, on the real
robot once it opens.
`g1lab` is the student package of the G1 Lab (Department of Mechanical Engineering,
The University of Iowa).

## Install

Python 3.8 or newer, somewhere with internet (the lab's Robot Network has none):

```
pip install "g1lab[camera,mock,missions] @ https://github.com/rstory1/g1lab/releases/download/v0.1.13/g1lab-0.1.13-py3-none-any.whl"
```

`camera` adds Pillow (camera pictures as arrays), `mock` adds MuJoCo (the laptop
robot) and `missions` adds PyYAML (mission files); leave out what you do not need.
Add `video` for OpenCV's live window and video files, about 190 MB more, and
`export` for turning recordings into a training set. Every extra and what needs it:
[docs/guide.md](docs/guide.md#install).

In the lab, plug into the Robot Network and set your address by hand:
[section 1 of the camera quickstart](docs/camera_quickstart.md#1-get-on-the-robot-network-and-watch-the-camera).

To update in the lab, once installed:
`pip install http://192.168.123.222:8090/g1lab-0.1.13-py3-none-any.whl`

Check you are ready: `python -m g1lab.check --host mock` anywhere, then
`python -m g1lab.check --name YOURNAME` in the lab. Each line says ok, note or FAIL,
with the fix: your Python and packages, the mock robot, your address, whether the lab
board serves the same g1lab as yours, the robot computer's ports 5600 and 5601, and the
session. It only reads; nothing moves.

## A first program

```python
import math
import time
import g1lab

r = g1lab.mock()                                   # in the lab: g1lab.connect("192.168.123.222", name="YOURNAME")
home = r.info().home                               # the robot's standing pose

arm = home["right_arm"].copy()
arm[0] = math.radians(-60)                         # shoulder_pitch: raise the arm forward
arm[3] = math.radians(20)                          # elbow

with r.control() as c:                             # waits for your turn
    c.arms.move_to(right=arm, duration=2.0)        # smoothly, over 2 s
    c.hands.close("right")
    time.sleep(5)                                  # the arm stays up: g1lab keeps sending
# leaving the block lets go: the arms go home
r.close()
```

## What you can call

`help()` on any of these says more. Reading works any time, without a turn.

| Read | Gives |
|---|---|
| `r.state.joints()` | `.q`, `.target`, `.temp` of all 29 joints; `.arm("right")`; `js["R_elbow"]` |
| `r.state.imu()` | body tilt: `.rpy` (rad), `.quat` |
| `r.state.temps()` | `["hottest"]`, `["body"]`, `["hand_r"]`, `["hand_l"]` (deg C) |
| `r.hands.state("right")` | `.q`, `.pads` (touch, named by `.pad_names`), `.temp` |
| `r.camera.read()`, `r.camera.jpeg()` | `(t, picture)` as an RGB array or JPEG bytes |
| `r.depth.read()` | `(t, xyz, rgb)` 3-D points from the camera; robot only |
| `r.lidar.read()` | `.points()`: the lidar's points. The walking mock and the walking simulator give a flat scan; the robot's 3-D lidar is not switched on yet |
| `r.lidar.imu()` | `.stamp`, `.gyro`, `.acc`: the lidar's own IMU; not switched on yet |
| `r.state.tf()` | where the lidar and camera sit on the body; not switched on yet |
| `r.on("joints", f)` | calls `f(value)` on each new reading; returns a function that stops it |
| `r.info()` | `.home`, `.limits`, `.groups`, `.owner`, `.queue` |
| `r.session()` | `.phase`, `.owner`, `.queue`, `.time_left` |
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
`Busy` (someone else has the robot), `NoSession`, `NoData` (that sensor is not
sending), `Disconnected`, `Ended` (your session is over).

`r.services.start("sim")` asks the robot computer for a simulated robot.

`r.ask("your question")` returns the language model's answer as text; it runs on the
robot computer and is refused while the real robot runs. The first question can take a
minute. On the mock it answers with a line saying there is no model.

## Record a dataset

Saves the sensors to a folder and reads them back on one clock, so each lidar frame
pairs with the right joints. It only listens, so it needs no turn and the robot does
not move. About 1.5 MB a second without depth.

```python
import g1lab

with g1lab.connect("192.168.123.222", name="YOURNAME") as r:
    rec = g1lab.Recorder(r, "run1").run(60)        # 60 s

print(rec)                                         # what it got, and any gaps
for t, cloud in rec.read("lidar"):
    joints = rec.at("joints", t)                   # the joints at that moment
```

Or with no program: `python -m g1lab.record --host 192.168.123.222 --seconds 60 --out run1`
(`--host mock` records the mock's joints on a laptop). Add `--depth` for depth, and
`python -m g1lab.record show run1` to see what is in a recording.

Recordings become a LeRobot training set, one folder per demo, with your own rule
for which demos worked (add `export` to the extras in the install line):

```
python -m g1lab.export run1 run2 run3 --out pick --task "pick up the cube" --success mine.py
```

[docs/guide.md](docs/guide.md#turning-recordings-into-a-training-set) says what goes in `mine.py`.

## Walk, reach and run missions

In the lab these run in the walking simulator, which your program starts with
`r.services.start("walk")`; not on the real robot yet. On a laptop:

```python
import g1lab

r = g1lab.mock(name="YOURNAME", nav="lab")       # a pretend room; arms=True lets the arms carry too
p = r.nav.pose()                                 # x, y (m), yaw (rad) on the map
with r.control() as c:
    h = r.nav.go_to(p.x + 1.0, p.y, yaw=0.0)     # plan a route and walk it
print(h.result, h.reason)                        # "arrived", or why not
r.close()
```

`g1lab.reach` plans the right arm onto a point (`Unreachable` says why it cannot), and
`g1lab.mission` runs skills in a row (find, approach, pick, ...) from Python or a YAML
file. Every result, every
error and the safety rules: [docs/walk_reach_missions.md](docs/walk_reach_missions.md).

## More

- [docs/guide.md](docs/guide.md): every call, what each error means, the mock, the
  language model, recording.
- [docs/joints_and_messages.md](docs/joints_and_messages.md): which way each joint
  turns, what the robot does to keep everyone safe, and the plain messages under `g1lab`.
- [docs/policy.md](docs/policy.md): your own network or class driving the arms and
  hands 50 times a second, tried on the mock, then handed to the operator.
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
  `reach_basic.py`, `mission_basic.py` (with `mission_basic.yaml`) and
  `carry_while_walking.py`. Each but `zed_sdk.py` runs with no robot:
  `python examples/wave.py --host mock --name YOURNAME`
- What changed in each release: [CHANGELOG.md](CHANGELOG.md).

## Licence

`g1lab` is under the Apache License 2.0 ([LICENSE](LICENSE)). The wheel also carries
the Unitree G1 robot model and meshes, under their own terms: see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
