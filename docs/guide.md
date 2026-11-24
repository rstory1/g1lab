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

Python 3.8 or newer, anywhere with internet (the Robot Network has none):

```
pip install "g1lab[camera,mock,missions] @ https://github.com/rstory1/g1lab/releases/download/v0.1.17/g1lab-0.1.17-py3-none-any.whl"
```

That brings `pyzmq`, `msgpack` and `numpy`. Each name in the brackets is an extra;
leave out what you do not need, or add one by putting its name in the brackets:

| Extra | Adds | For |
|---|---|---|
| `camera` | Pillow | camera pictures as arrays (`r.camera.read()`), the mock's drawn camera |
| `mock` | MuJoCo | `g1lab.mock()`, the robot on your laptop |
| `missions` | PyYAML | mission files written in YAML |
| `video` | OpenCV, about 190 MB | a live camera window and video files; pictures and arrays work without it |
| `export` | pyarrow, OpenCV | `python -m g1lab.export`, recordings to a training set |
| `vision` | onnx, onnxruntime | `r.vision` on the mock: your own detector, run on your computer |

In the lab, the same file is on the **lab board**: open
`http://192.168.123.222:8090/` in a browser on the Robot Network, which also
shows who has the robot, who is next, and what the robot's camera sees.
There, with the dependencies already installed:

```
pip install http://192.168.123.222:8090/g1lab-0.1.17-py3-none-any.whl
```

### Check you are ready

```
python -m g1lab.check --host mock          # anywhere: Python, packages, the mock robot
python -m g1lab.check --name YOURNAME      # in the lab, on the Robot Network
```

One line per check, ok / note / FAIL, each with its fix: Python and g1lab, the
optional packages, the mock robot; in the lab also your address (.130-.159 by
hand), whether the lab board serves the same g1lab as yours, the command port
(5600), the streams (5601: which feeds are live) and the session, in words. A
missing extra or a different g1lab is a note; no answer from the robot computer
fails. It exits 1 when anything failed. It only reads: nothing moves.

## A first program

```python
import math
import time
import g1lab

r = g1lab.connect("192.168.123.222", name="YOURNAME")  # the robot computer, and your name
home = r.info().home                                   # the robot's standing pose

arm = home["right_arm"].copy()
arm[0] = math.radians(-60)                             # shoulder_pitch: raise the arm forward
arm[3] = math.radians(20)                              # elbow

with r.control() as c:                                 # waits for your turn
    c.arms.move_to(right=arm, duration=2.0)            # smoothly, over 2 s
    c.hands.close("right")
    time.sleep(5)                                      # the arm stays up: g1lab keeps sending
# leaving the block lets go: the arms go home, and the next student gets the robot
```

The joints, their order and which way they turn: see [Which way the joints turn](joints_and_messages.md#which-way-the-joints-turn).
Angles are in radians.

## Reading the robot

Reading works any time, without a session and without waiting your turn.

| Call | What you get |
|---|---|
| `r.info()` | `phase`, `owner` (who has the robot), `queue`, `backend` (`"robot"` or `"sim"`, `"mock"` on `g1lab.mock()`; None when there is no session), and for each group (`left_arm`, `right_arm`, `left_hand`, `right_hand`): `groups` (joint names), `limits` (low, high), `home` |
| `r.session()` | `phase`, `owner`, `queue`, `time_left` (seconds left in the session, counted from LIVE; None before LIVE and when there is no session) |
| `r.state.joints()` | all 29 joints: `q` (angles), `target`, `temp`. `js.arm("right")` gives the 7 arm angles in the usual order; `js["R_elbow"]` one joint |
| `r.state.imu()` | the body's tilt: `rpy` (roll, pitch, yaw) and `quat` |
| `r.state.temps()` | motor temperatures, and the `hottest` one |
| `r.hands.state("right")` | `q` (7 finger angles), `pads` (9 touch pads, names in `pad_names`; `None` in the simulator, which has none), `temp` |
| `r.camera.read()` | `(t, picture)`: an array of height × width × 3 colours (needs Pillow). `r.camera.jpeg()` gives the JPEG file instead |
| `r.depth.read()` | `(t, xyz, rgb)`: 3-D points in metres and their colours |
| `r.depth.image()` | `(t, depth)`: a distance in metres for every pixel of the camera picture, `NaN` where it could not measure. **Needs `r.services.start("zed")`**: see [the camera quickstart](camera_quickstart.md#7-depth-for-every-pixel-and-the-zeds-objects-bodies-and-pose) |
| `r.zed.objects()`, `r.zed.bodies()`, `r.zed.pose()` | what the ZED SDK works out from the camera: the things and people it sees (boxes and skeletons, in 3-D and on the picture) and where the camera is. Also needs `r.services.start("zed")` |
| `r.on("joints", f)` | calls `f(js)` for every new reading, in the background. Also `"imu"`, `"hands.right"`, `"hands.left"`, `"temps"`, `"camera"`, `"depth"`, `"depth.image"`, `"lidar"`, `"head_imu"`, `"tf"`, `"zed.objects"`, `"zed.bodies"`, `"zed.pose"`, `"session"`, `"health"`, and in a walking session `"pose"` and `"odom"`. It returns a function: call it to stop |
| `r.nav.pose()`, `r.nav.odom()` | in a walking session: where the robot is on the map, and where its legs count it is (starts at 0, 0, 0 and drifts). See [walk_reach_missions.md](walk_reach_missions.md) |

A read gives the newest reading. If a sensor has sent nothing for a while,
the read waits up to 2 seconds and then raises `NoData`.

### The lidar

The walking mock (`g1lab.mock(nav="lab")`) and the walking simulator answer
`r.lidar.read()` with a flat `Scan`: one turn of 360 beams in the body's frame
(0 = ahead, +90° = left), `inf` where nothing came back; `scan.points()` gives the
points. The real robot's 3-D lidar on its head is not switched on yet. Once it is,
these calls read it, with no session, like the camera:

| Call | What you get |
|---|---|
| `r.lidar.read()` | a `Cloud`: `xyz` (up to 4,000 points, metres, in the lidar's frame `livox_frame`), `intensity` (0 to 255), `t`. 10 times a second. `cloud.points()` gives the `xyz` |
| `r.lidar.imu()` | the lidar's own motion sensor: `gyro` (rad/s) and `acc` (m/s², gravity included), several samples per reading with their times in `stamp`. The gyro reads about 0.06 rad/s (3°/s) when the robot is still: average it for a second or two at rest and subtract that before adding up turns |
| `r.state.tf()` | where each part of the robot is relative to the next (`transforms`: `parent`, `child`, `xyz`, `quat` as w, x, y, z), for turning lidar points into the body's frame |

The points are thinned to about one per 4 in cube, so a reading is light
enough for Wi-Fi. Code that only uses `.points()` works on both.

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
| `c.walk(vx, vy, wz)`, `c.stop()` | in a walking session only: walk for half a second (forward, left, turning), or stop now. See [walk_reach_missions.md](walk_reach_missions.md) |

`r.control()` first waits for your turn. It prints why it is waiting (*ben
has the robot; you are 1st in line*) and goes on by itself when your turn
comes. It waits 10 minutes at most; `r.control(wait=60)` waits less. Then
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
them back, all on one clock. It needs no session and the robot does not move.
The computer running your program must stay on the Robot Network, and the
recording lands on that computer. Record over a cable plugged into a Robot
Network switch port, not Wi-Fi: about 1.5 MB arrives every second, and a
dropped reading leaves a gap that rejects the demo at export.

```python
import g1lab

run = g1lab.Recorder("192.168.123.222", "hallway").run(seconds=30)
# on a laptop: g1lab.Recorder(g1lab.mock(camera="render"), "hallway")
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
| `Recorder(source, out, topics)` | `source` is the robot computer's address, or a connected robot or mock. `out` is a new folder (default `recording_<date>_<time>`). `topics` narrows what is kept; the default is everything but depth and the ZED topics (`depth.image`, `zed.objects`, `zed.bodies`, `zed.pose`), and `g1lab.recording.ALL_TOPICS` adds them. The robot's lidar is off, so its `lidar` topic records nothing there. It stops by itself with less than 1 GB left on the disk |
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
load a TorchScript file, and the tools to try it on the mock. You send the
folder with `r.policy.upload()` and trial it in a simulator session with
`r.policy.trial()`; the operator approves a passing hash and runs it on the robot
with you. See [policy.md](policy.md).

## When something goes wrong

Each problem is its own exception, so you can catch the one you expect:

| Exception | What it means | What to do |
|---|---|---|
| `Disconnected` | no answer from the robot computer: the address is wrong, or the robot computer is not running | check the address (in the lab: `192.168.123.222`) |
| `NoSession` | the robot computer answers, but no session is running | start a simulator session with `r.services.start("sim", wait=120)`, or wait: `control()` waits for one |
| `Busy` | someone else has the robot (`e.owner`, your place `e.place`) | `control()` waits your turn; this comes only when `wait` runs out |
| `NameInUse` | someone on another computer uses your name | pick another `name` |
| `Refused` | the pose would hit the robot itself (`e.reason` says what) | change that arm's angles. `move_to` raises it; after `set` it shows on `c.status.refused` |
| `Ended` | the session is over, or ending | stop; your program is done |
| `NoData` | a sensor sent nothing | that sensor is off, or the session does not carry it |
| `ServiceRefused` | `r.services.start()` may not start that service (`e` says why) | the reason says which. Graphics card too full (`llm`, `zed`): stop your own other service or try again later; the reason gives the numbers. "not available yet": there is no such service yet. Session or deployment services: they start only from the launcher, so start `"sim"` or `"walk"` instead |

They all belong to `g1lab.G1LabError`.

```python
try:
    c.arms.move_to(right=arm)
except g1lab.Refused as e:
    print("not that pose:", e.reason)
```

## Starting a simulator or the language model: `r.services`

A program can ask the robot computer to start what it needs. No session is
needed for this.

```python
r.services.start("sim", wait=120)    # a simulated robot for your program; returns when it takes programs (about 30 s)
with r.control() as c:               # then use it as usual
    ...
r.services.start("llm", wait=120)    # the language model on the robot computer
r.services.start("zed", wait=180)    # the ZED's depth image, objects, bodies and pose (r.zed); usually a few seconds, up to a minute the first time
print(r.services.status("llm"))      # ServiceInfo(name='llm', state='running', programs=1, ...)
r.services.stop("llm")               # you are done with it
print(r.services.status())           # every service: what it is, and whether it runs
```

- **sim** is a simulator session that only ever drives the simulated robot.
  `start("sim", wait=N)` returns when the session takes programs, or raises "the simulator is
  still starting: wait a little longer, or start with a larger wait=" (a `g1lab.G1LabError`) when N runs out.
  Only one runs at a time, and never while the real robot is on.
- **walk** is the same kind of session with the simulated robot walking: see
  [walk_reach_missions.md](walk_reach_missions.md). It and `sim` share
  one simulator, so only one of the two runs.
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
- **deploy, session** move the robot. Only the
  operator starts them, from the launcher; `start()` raises
  `g1lab.ServiceRefused` saying so.
- **vision, speech, recorder** are not available: `start()` says "not available yet".
  Your own detector needs no service: `r.vision` (see
  [Your own detector](#your-own-detector-rvision)). Recording runs from your own program
  on your own computer; see [Recording a dataset](#recording-a-dataset).

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

On a laptop, `g1lab.mock()` answers these with the same rules and starts nothing.

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
this works from a laptop. It only writes text: it cannot move the robot, and it
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

On the mock, `r.ask()` answers with a line saying it has no model. To test a
program that acts on the answer, give it one:
`g1lab.mock(name="YOURNAME", llm=lambda prompt: "wave")`.

## On a laptop: `g1lab.mock()`

No robot, no network: `r = g1lab.mock(name="YOURNAME")` answers every call
`connect()` does, and runs the robot's own safety code, so a pose the robot
refuses is refused here too, with the same words. Most examples take
`--host mock`; `mission_basic.py` has no `--host` (it runs on the mock), and `zed_sdk.py` has no mock. Needs the `mock` extra ([Install](#install)).

```python
r = g1lab.mock(name="YOURNAME", view=True)  # view: a 3-D window with the robot's pose
with r.control() as c:
    c.arms.move_to(right=..., duration=2.0)
```

What it is not: the legs stand still, nothing balances or heats up, the hand
pads read zero, and the camera plays a short recorded clip (or nothing).
`g1lab.mock(camera="render")` draws the head camera's view instead: the
mock robot's own arms and a red ball in front of the right shoulder
(`ball=(x, y, z)` moves it, `ball=None` removes it; needs the `camera` extra). The
simulated camera sits where the robot's camera sits, with the same lens, so
pixel maths that works here works on the robot.
`r.vision` runs your own detector on that camera, here on your computer
([Your own detector](#your-own-detector-rvision)).
Joints follow the command about 0.1 s behind, as on the robot. The session
runs like a real one: settling for 2 s after your first pose, then live, and
after `minutes=` (45) the arms go home and it ends. `say=print` shows the
robot computer's own messages ("pose held: ...", "arm resting"). On a Mac,
run a program with `view=True` using `mjpython` instead of `python`.

`g1lab.mock(nav="lab")` (an 8 x 6 m room) or `nav="hall"` (a 20 m corridor with doors)
makes the mock a walking session: see [walk_reach_missions.md](walk_reach_missions.md).

## Example programs

Small programs to start from are in [examples/](../examples/). Each says at its top what it
does and how to run it; all but `zed_sdk.py` run on a laptop with `--host mock`.
[walk_reach_missions.md](walk_reach_missions.md) explains the walking, reach and
mission ones.

## Missions

Skills in a row (find, go_to, approach, pick, place, drop, home), from a YAML file or
from Python: [missions.md](missions.md).

## Your own detector: `r.vision`

Upload an ONNX model you trained, and each camera picture goes through it; your program
reads what it found, each thing with a 3-D point. It runs on `g1lab.mock(camera="render")`
today, and on the robot once that is switched on: [vision.md](vision.md).

## Modules

The modules, worked notebooks that each show how to use one feature and run on the
mock first, are in [notebooks/](../notebooks/README.md); that page lists
them and says what to install.
