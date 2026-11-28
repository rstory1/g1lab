# g1lab: drive and read the G1 from Python

`g1lab` is a small Python package for your own robot programs. It does the
fiddly parts of [the plain messages](joints_and_messages.md) for you. Inside
`with r.control() as c:` it sends your pose about 30 times a second, so the arms
do not go down when your program stops to think, print or draw a plot. Each
problem comes back as its own named error: see
[When something goes wrong](#when-something-goes-wrong).

**Moving the arms runs on the simulated robot for now; reading the camera, depth and
the ZED already works on the real robot.** Your program does not change when the arms
open on the real one.

## Install

Python 3.8 or newer. You run your programs logged in on the lab workstation with your university ID, and
g1lab is installed in your own account there, from the wheel (a virtual environment keeps it yours):

```
python3 -m venv ~/g1lab-env && . ~/g1lab-env/bin/activate
pip install "g1lab[camera,missions] @ https://github.com/rstory1/g1lab/releases/download/v0.1.20/g1lab-0.1.20-py3-none-any.whl"
```

That brings `pyzmq`, `msgpack` and `numpy`. Each name in the brackets is an extra;
leave out what you do not need, or add one by putting its name in the brackets:

| Extra | Adds | For |
|---|---|---|
| `camera` | Pillow | camera pictures as arrays (`r.camera.read()`) |
| `missions` | PyYAML | mission files written in YAML |
| `video` | OpenCV, about 190 MB | a live camera window and video files; pictures and arrays work without it |
| `export` | pyarrow, OpenCV | `python -m g1lab.export`, recordings to a training set |

The same file is on the **lab board**: open `http://192.168.123.222:8090/` in a browser,
which also shows whether a program is moving the robot, whose, and what the robot's camera sees.
To install it from there, with the dependencies already installed:

```
pip install http://192.168.123.222:8090/g1lab-0.1.20-py3-none-any.whl
```

### Check you are ready

```
python -m g1lab.check
```

One line per check, ok / note / FAIL, each with its fix: Python and g1lab, the
optional packages, your address, whether the lab board serves the same g1lab as yours, the command port
(5600), the streams (5601: which feeds are live), whether the robot is on and which features are on, in words. A
missing extra or a different g1lab is a note; no answer from the robot computer
fails. It exits 1 when anything failed. It only reads: nothing moves.

## A first program

```python
import math
import time
import g1lab

r = g1lab.connect()                                    # the lab workstation, as the account you are logged in with
r.services.start("sim", wait=120)                      # the arm simulator; about 30 s the first time
print(r.info().features)                               # what you can do right now, and why anything is off
home = r.info().home                                   # the robot's standing pose

arm = home["right_arm"].copy()
arm[0] = math.radians(-60)                             # shoulder_pitch: raise the arm forward
arm[3] = math.radians(20)                              # elbow

with r.control() as c:                                 # waits until nobody else is moving the robot
    c.arms.move_to(right=arm, duration=2.0)            # smoothly, over 2 s
    c.hands.close("right")
    time.sleep(5)                                      # the arm stays up: g1lab keeps sending
# leaving the block lets go: the arms go home, and the robot is free for the next program
```

`print(r.info().features)` prints one line per feature, `on` or `off: ` and the reason. Before you call
something, ask: `r.info().features["walking"].on` is `True` when `c.walk()` will work. See
[What is on](#what-is-on-rinfofeatures).

The joints, their order and which way they turn: see [Which way the joints turn](joints_and_messages.md#which-way-the-joints-turn).
Angles are in radians.

## Reading the robot

Reading works any time, with the robot off and while another program is moving the robot.

| Call | What you get |
|---|---|
| `r.info()` | `robot` (`"off"`, `"sim"` for a simulator, or `"robot"`), `features` (what is on: see below), `owner` (who has the robot), `time_left` (seconds left in the run the operator set, counted from LIVE; None before LIVE and when there is no limit), and for each group (`left_arm`, `right_arm`, `left_hand`, `right_hand`): `groups` (joint names), `limits` (low, high), `home` |
| `r.state.joints()` | all 29 joints: `q` (angles), `target`, `temp`. `js.arm("right")` gives the 7 arm angles in the usual order; `js["R_elbow"]` one joint |
| `r.state.imu()` | the body's tilt: `rpy` (roll, pitch, yaw) and `quat` |
| `r.state.temps()` | motor temperatures, and the `hottest` one |
| `r.hands.state("right")` | `q` (7 finger angles), `pads` (9 touch pads, names in `pad_names`; `None` in the simulator, which has none), `temp` |
| `r.camera.read()` | `(t, picture)`: an array of height × width × 3 colours (needs Pillow). `r.camera.jpeg()` gives the JPEG file instead |
| `r.depth.read()` | `(t, xyz, rgb)`: 3-D points in metres and their colours |
| `r.depth.image()` | `(t, depth)`: a distance in metres for every pixel of the camera picture, `NaN` where it could not measure. **Needs `r.services.start("zed")`**: see [the camera quickstart](camera_quickstart.md#7-depth-for-every-pixel-and-the-zeds-objects-bodies-and-pose) |
| `r.zed.objects()`, `r.zed.bodies()`, `r.zed.pose()` | what the ZED SDK works out from the camera: the things and people it sees (boxes and skeletons, in 3-D and on the picture) and where the camera is. Also needs `r.services.start("zed")` |
| `r.on("joints", f)` | calls `f(js)` for every new reading, in the background. Also `"imu"`, `"hands.right"`, `"hands.left"`, `"temps"`, `"camera"`, `"depth"`, `"depth.image"`, `"lidar"`, `"head_imu"`, `"tf"`, `"zed.objects"`, `"zed.bodies"`, `"zed.pose"`, `"session"`, `"health"`, and with walking on `"pose"` and `"odom"`. It returns a function: call it to stop |
| `r.nav.pose()`, `r.nav.odom()` | with walking on: where the robot is on the map, and where its legs count it is (starts at 0, 0, 0 and drifts). See [walk_reach_missions.md](walk_reach_missions.md) |

A read gives the newest reading. If a sensor has sent nothing for a while,
the read waits up to 2 seconds and then raises `NoData`.

### What is on: `r.info().features`

The robot is off, or it is a simulator, or it is the real robot (`r.info().robot`). What it can do is a
set of features, each on or off. `r.info().features` maps a name to an object with `.on` (True or
False) and `.why`: empty when on, and when off one sentence saying why and what turns it on.
`print(r.info().features)` shows them all. A feature the robot computer cannot tell is not in the list.

| Feature | What it covers | What turns it on |
|---|---|---|
| `arms` | arm and hand poses (`c.arms`, `c.hands`) | the arm simulator: `r.services.start("sim", wait=120)`. Off while the robot walks (walking takes `walk()` only), while the operator drives the arms, and after a fall until the operator clears it |
| `walking` | `c.walk()`, `r.nav`, `r.nav.go_to()` | the walking simulator: `r.services.start("walk", wait=300)`, with the arm simulator off. Not open to programs on the real robot yet |
| `camera` | the head camera's pictures | on with either simulator a few seconds after it starts, and on the real robot when the operator has the camera running |
| `policy_trial` | `r.policy.trial()` | a simulator on, and the policy service on the robot running. Not on the real robot |
| `teleop` | the operator driving the arms | only the operator, from the launcher. While it is on, `arms` is off |

```python
f = r.info().features
if not f["walking"].on:
    print(f["walking"].why)       # e.g. "walking is off: the arm simulator is on, and it cannot walk. Turn it off with ..."
```

When a call needs something that is off, it raises `Off` (see
[When something goes wrong](#when-something-goes-wrong)); its message is the same sentence.

### The lidar

The walking simulator answers
`r.lidar.read()` with a flat `Scan`: one turn of 360 beams in the body's frame
(0 = ahead, +90° = left), `inf` where nothing came back; `scan.points()` gives the
points. The real robot's 3-D lidar on its head is not switched on yet. Once it is,
these calls read it, with the robot off, like the camera:

| Call | What you get |
|---|---|
| `r.lidar.read()` | a `Cloud`: `xyz` (up to 4,000 points, metres, in the lidar's frame `livox_frame`), `intensity` (0 to 255), `t`. 10 times a second. `cloud.points()` gives the `xyz` |
| `r.lidar.imu()` | the lidar's own motion sensor: `gyro` (rad/s) and `acc` (m/s², gravity included), several samples per reading with their times in `stamp`. The gyro reads about 0.06 rad/s (3°/s) when the robot is still: average it for a second or two at rest and subtract that before adding up turns |
| `r.state.tf()` | where each part of the robot is relative to the next (`transforms`: `parent`, `child`, `xyz`, `quat` as w, x, y, z), for turning lidar points into the body's frame |

The points are thinned to about one per 4 in cube, so a reading is light
enough to stream. Code that only uses `.points()` works on both.

## Moving the robot

Everything that moves the robot goes inside `with r.control() as c:`.

| Call | What it does |
|---|---|
| `c.arms.move_to(right=q, duration=2.0)` | moves there smoothly and returns when it is there. `left=` too, or both |
| `c.arms.set(right=q)` | the new pose, at once. Use it in a loop for your own motion |
| `c.arms.home()` | both arms back to the standing pose |
| `c.hands.close("right")` | a fist. `c.hands.close("right", 0.5)` half closed; `"both"` for both hands |
| `c.hands.open("right")` | open |
| `c.hands.set("left", q)` | your own 7 finger angles |
| `c.status` | the robot's last answer: `phase`, `clamped`, `held`, `resting`, `refused` |
| `c.walk(vx, vy, wz)`, `c.stop()` | with walking on only: walk for half a second (forward, left, turning), or stop now. See [walk_reach_missions.md](walk_reach_missions.md) |

`r.control()` first waits until the robot is free. Only one program moves it at a time; the
others' motion commands are refused, and `control()` keeps trying. It prints why it is waiting
(*the robot is in use by `<login>`; it is free when that program ends or lets go*) and goes on by itself
when the robot is free. Two programs run by the same login count as one and share the robot.
It waits 10 minutes at most; `r.control(wait=60)` waits less. Then
the robot eases into its standing pose, which takes a few seconds, and the
block starts.

`c.status` tells you:

- `clamped`: you asked for more than a joint can do; the robot went as far as it is allowed;
- `held`: the arms stopped part way, because going on would hit something;
- `resting`: an arm was up too long and is resting by its side, for the seconds shown. `c.status.reply.get("resting_why")` says when the raised time came from the program before yours (the 30 s count is the robot's, shared by whoever drives);
- `refused`: the last pose was refused, and why. It goes back to None when a pose is taken again.
  The arms hold the last safe pose, and a `move_to` or `home()` after a refused `set` starts from there.

## Recording a dataset

`g1lab.Recorder` writes the sensors to a folder, and `g1lab.Recording` reads
them back, all on one clock. It works with the robot off, and the robot does not move.
The recording lands in a folder on the computer that runs your program, in your
own account on the lab workstation. About 1.5 MB arrives every second, and a
dropped reading leaves a gap that rejects the demo at export.

```python
import g1lab

run = g1lab.Recorder("192.168.123.222", "hallway").run(seconds=30)
print(run)                                     # what it holds, per sensor
for t, picture in run.read("camera"):
    joints = run.at("joints", t, max_age=0.1)  # (time, joints) at that moment
```

To record while your program does something else, use `with
g1lab.Recorder(...):` around that code. To read a folder later,
`g1lab.Recording("hallway")`.

From a terminal: `python -m g1lab.record --host 192.168.123.222 --seconds 60
--out hallway`, then `python -m g1lab.record show hallway`.

| Call | What you get |
|---|---|
| `Recorder(source, out, topics)` | `source` is the robot computer's address, or a connected robot. `out` is a new folder (default `recording_<date>_<time>`). `topics` narrows what is kept; the default is everything but depth and the ZED topics (`depth.image`, `zed.objects`, `zed.bodies`, `zed.pose`), and `g1lab.recording.ALL_TOPICS` adds them. The robot's lidar is off, so its `lidar` topic records nothing there. It stops by itself with less than 1 GB left on the disk |
| `rec.run(seconds)`, `rec.start()`, `rec.stop()`, `rec.counts()` | record for that long (until Ctrl-C with no number); start and stop in the background (`stop()` and `run()` return the Recording); readings so far, per sensor |
| `run.read(topic, start, end)` | every reading in that time span as `(t, value)` |
| `run.at(topic, t, max_age)` | the newest reading at or before `t` as `(t, value)`, `None` if none is that recent |
| `run.play(topics, start, end)` | `(t, topic, value)` across sensors, in time order |
| `run.stamps(topic)` | all of a sensor's times, as an array |
| `run.topics`, `run.t0`, `run.t1`, `run.duration`, `run.summary()` | what the folder holds |
| `run.backend` | `"robot"` or `"sim"`: what it was recorded from (`None` if the recording does not say) |

A camera value is the picture, a depth value is `(xyz, rgb)`, a `depth.image` value is the depth image (`run.topics` and `run.play()` name it `zed.depth`), and every other
value comes back as the same kind of object the live read gives (`JointState`, `Imu`, and so on). Pass `raw=True` to get the
stored message (a plain dictionary) instead, untouched.

**Size:** about 1.5 MB a second, so a minute is about 90 MB. Depth adds about
0.9 MB a second. **The clock:** every `t` is the robot computer's clock. Camera
pictures are stamped about 50 ms before they arrived, when the robot took them.

### Turning recordings into a training set

One recording folder is one demo. `python -m g1lab.export` turns a set of them
into a LeRobot v2.1 dataset, with a label for each demo saying whether it worked.

It needs the `export` extra ([Install](#install)):

```
python -m g1lab.export pick_01 pick_02 pick_03 --out pick --task "pick up the cube" --success mine.py
```

`mine.py` holds your rule for a good demo, which gets the `Recording`:

```python
def success(rec):
    t, joints = rec.at("joints", rec.t1)
    return joints["L_sh_pitch"] < -0.5
```

`--only-success` leaves the failed demos out. `--label true` or `--label false`
gives them all the same label. Without either, the label is null.

Each frame's state is the 29 body joints, both hands and projected gravity (46
numbers). Its action is the body joints one frame later and both hands' commanded
joints (43 numbers). The picture is the head camera at 15 frames a second, so
record with the camera on. An export needs a new output folder. A gap in the joint
readings rejects the demo: split or re-record it instead of joining states across a gap.
All kept demos must have the same camera coverage and image dimensions. You can
export camera-free demos together, but they form a state-only dataset. Video and
state timestamps use the same requested frame rate (`--fps`, default 15).

## Policies

A policy is your network or Python class driving the arms and hands 50 times a
second. `g1lab.policy` holds the `Policy` class to write one, `NetworkPolicy` to
load a TorchScript file, and the tools to try it in your own program. You send the
folder with `r.policy.upload()` and trial it in a simulator with
`r.policy.trial()`; the operator approves a passing hash and runs it on the robot
with you. See [policy.md](policy.md).

## When something goes wrong

Each problem is its own exception, so you can catch the one you expect:

| Exception | What it means | What to do |
|---|---|---|
| `Disconnected` | no answer from the robot computer: the address is wrong, or the robot computer is not running | check the address (in the lab: `192.168.123.222`) |
| `Off` | the robot is off, or the feature this call needs is off. `e.feature` names the feature (`"walking"`, `"arms"`, `"policy_trial"`), and is None when the whole robot is off | read the message: it says what turns it on. With the robot off, `r.services.start("sim", wait=120)` turns the arm simulator on, or wait: `control()` waits for the robot. `r.info().features` shows every feature and why |
| `Busy` | someone else has the robot (`e.owner`), or you lost it | `control()` keeps trying; this comes only when `wait` runs out |
| `Refused` | the pose would hit the robot itself (`e.reason` says what) | change that arm's angles. `move_to` raises it; after `set` it shows on `c.status.refused` |
| `Ended` | the robot was turned off, or your control of it ended | stop; your program is done |
| `NoData` | a sensor sent nothing | that sensor is off, or the robot does not carry it |
| `ServiceRefused` | `r.services.start()` may not start that service (`e` says why) | the reason says which. Graphics card too full (`llm`, `zed`): stop your own other service or try again later; the reason gives the numbers. "not available yet": there is no such service yet. Services that move the robot (the deployment and the robot's walking services): they start only from the launcher, so start `"sim"` or `"walk"` instead. `"sim"` while the walking simulator runs, or `"walk"` while the arm simulator runs: the lab runs one simulator at a time; the message says which is running, and `r.services.stop(...)` of that one frees it a few seconds later |

They all belong to `g1lab.G1LabError`.

```python
try:
    c.arms.move_to(right=arm)
except g1lab.Refused as e:
    print("not that pose:", e.reason)
```

## Starting a simulator or the language model: `r.services`

A program can ask the robot computer to start what it needs. The robot can be off
for this.

```python
r.services.start("sim", wait=120)    # the arm simulator; returns when it takes programs (about 30 s)
with r.control() as c:               # then use it as usual
    ...
r.services.start("llm", wait=120)    # the language model on the robot computer
r.services.start("zed", wait=180)    # the ZED's depth image, objects, bodies and pose (r.zed); usually a few seconds, up to a minute the first time
print(r.services.status("llm"))      # ServiceInfo(name='llm', state='running', programs=1, ...)
r.services.stop("llm")               # you are done with it
print(r.services.status())           # every service: what it is, and whether it runs
```

- **sim** is the arm simulator: it only ever drives the simulated robot.
  `start("sim", wait=N)` returns when it takes programs, or raises "the simulator is
  still starting: wait a little longer, or start with a larger wait=" (a `g1lab.G1LabError`) when N runs out.
  Only one runs at a time, and never while the real robot is on.
- **walk** is the walking simulator: the simulated robot walking, see
  [walk_reach_missions.md](walk_reach_missions.md). It and `sim` share
  one simulator, so only one of the two runs. Asking for the other one while one runs raises
  `ServiceRefused` saying which is running and to stop it with `r.services.stop("sim")` or
  `r.services.stop("walk")` first; in a program that does not catch it, that sentence is all
  that prints and the program exits with an error. The arms work in both.
- **llm** is the language model. It needs about 22.5 GB of the
  graphics card, and the robot's controller must always keep 2 GB, so it is
  refused when the card is too full (the reason gives the numbers), and
  while the real robot is running, since it would slow the robot's controller.
- **zed** is the ZED SDK's depth image, objects, bodies and pose (`r.depth.image()`,
  `r.zed.objects()`, `r.zed.bodies()`, `r.zed.pose()`). It takes about 3 GB of the
  graphics card and is refused, with the numbers, when
  the card cannot also keep the robot's controller its 2 GB. Unlike the model it
  is allowed while the real robot runs, but it shares the card with the controller,
  so stop it when you are done. See [the camera quickstart](camera_quickstart.md#7-depth-for-every-pixel-and-the-zeds-objects-bodies-and-pose).
- The services named `deploy` and `session` move the robot. Only the
  operator starts them, from the launcher; `start()` raises
  `g1lab.ServiceRefused` saying so.
- **vision, speech, recorder** are not available: `start()` says "not available yet".
  Your own detector (`r.vision`) waits for the lab simulator too. Recording runs from your own program;
  see [Recording a dataset](#recording-a-dataset).

`start()` holds a lease for your program, and g1lab renews it every minute
while your program runs. Ten minutes after the last program using a service
stops (or calls `stop()`), the robot computer stops it. So running your
program again a minute later finds it still up. A service the operator
started from the launcher keeps running until the operator stops it.

`ServiceRefused` is a `G1LabError`, with the reason as its message:

```python
try:
    r.services.start("llm")
except g1lab.ServiceRefused as e:
    print(e)        # "the language model needs about 22.5 GB ... 13.2 GB is free; ..."
```

## Asking the language model: `r.ask()`

```python
answer = r.ask("Name one thing a robot arm can pick up with a pinch grip.")
print(answer)

reply = r.ask(f"The user said: {heard!r}. Answer with one word: wave or nod.",
              system="You choose one gesture. Reply with that word and nothing else.",
              max_tokens=5)
if reply.strip().lower() == "wave":
    ...
```

`r.ask()` returns the model's text. The model runs on the robot computer, so
this works from your own program. It only writes text: it cannot move the robot, and it
knows nothing about the robot, your program or your last question, so put
everything it needs in `prompt`, and the instruction it should keep to in
`system`. Check what comes back before acting on it. It can answer something
other than what you asked for.

- **The model does not run beside the real robot.** It would slow the robot's
  controller, so while the real robot is running `r.ask()` raises
  `ServiceRefused`. In the simulator it runs as usual.
- **The first question starts the model** if it is not running, which takes
  up to a minute; later ones skip that. It stays up for ten minutes after your
  program ends, as `r.services` describes.
- **The answer stops at `max_tokens`** (default 512, most 2048; a word is one
  or two tokens). `answer.truncated` is `True` when it was cut off, and
  `answer.seconds` is how long it took.
- **A question takes seconds, and longer behind others.** Questions go one at a
  time, in order. Each program has one at a time, and at most eight wait in line.
  `timeout` (default 120 s) is how long `r.ask()` waits. A program moving the
  arms keeps the arms moving from another thread: a question holds up only the
  line of your program that asked it.
- **A prompt can be 32,000 characters**, about 8,000 tokens.

```python
try:
    answer = r.ask("...")
except g1lab.ServiceRefused as e:
    print(e)        # the graphics card is too full (with the numbers), or the real robot is running
except g1lab.G1LabError as e:
    print(e)        # no answer in time, or the question was refused, with the reason
```

## Example programs

Small programs to start from are in [examples/](../examples/). Each says at its top what it
does and how to run it. They connect to the lab computer, `192.168.123.222`, unless you pass
`--host`.
[walk_reach_missions.md](walk_reach_missions.md) explains the walking, reach and
mission ones.

## Missions

Skills in a row, from a YAML file or from Python. In the lab simulator the `go_to` and `home` steps run
(`go_to` in the walking simulator, `home` in both); the ones that need a detector (`find`, `approach`, `pick`, `place`) wait
for one: [missions.md](missions.md).

## Modules

The modules, worked notebooks that each show how to use one feature, are in [notebooks/](../notebooks/README.md); that page lists
them and says what to install.
