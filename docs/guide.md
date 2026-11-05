# g1lab: drive and read the G1 from Python

`g1lab` is a small Python package for your own robot programs. It does the
fiddly parts of [the plain messages](joints_and_messages.md) for you:

- **It keeps sending.** Inside `with r.control() as c:` it sends your pose
  about 30 times a second, so the arms don't go down when your program stops
  to think, print or draw a plot.
- **It never mixes up the answers.** You never see "Operation cannot be
  accomplished in current state".
- **It tells you what went wrong by name:** your turn hasn't come, the pose
  was refused, the session is over.
- **It reads the sensors:** the joints, the body's tilt, the hands, the
  temperatures, the camera and the 3-D points.

**Right now this runs on the simulated robot.** Your program does not change
when it moves to the real one.

## Install

Anywhere with internet (the Robot Network has none):

```
pip install "g1lab[camera,mock] @ https://github.com/rstory1/g1lab/releases/download/v0.1.5/g1lab-0.1.5-py3-none-any.whl"
```

That brings `pyzmq`, `msgpack` and `numpy`; `camera` adds `pillow` (camera
pictures as arrays) and `mock` adds `mujoco` (the laptop robot). To show a
live camera window or write video files you also need OpenCV (about 190 MB);
to include it:

```
pip install "g1lab[camera,mock,video] @ https://github.com/rstory1/g1lab/releases/download/v0.1.5/g1lab-0.1.5-py3-none-any.whl"
```

Without it, pictures, arrays and datasets of pictures still work. The
examples and the camera quickstart are at https://github.com/rstory1/g1lab.

In the lab, the same file is on the **lab board**: open
`http://192.168.123.222:8090/` in a browser on the Robot Network, which also
shows who has the robot, who is next, and what the robot's camera sees.
There, with the dependencies already installed:

```
pip install http://192.168.123.222:8090/g1lab-0.1.5-py3-none-any.whl
```

It needs Python 3.8 or newer.

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
| `r.info()` | `phase`, `owner` (who has the robot), `queue`, and for each group (`left_arm`, `right_arm`, `left_hand`, `right_hand`): `groups` (joint names), `limits` (low, high), `home` |
| `r.session()` | `phase`, `owner`, `queue`, `time_left` (seconds left in the session, counted from LIVE; None before LIVE) |
| `r.state.joints()` | all 29 joints: `q` (angles), `target`, `temp`. `js.arm("right")` gives the 7 arm angles in the usual order; `js["R_elbow"]` one joint |
| `r.state.imu()` | the body's tilt: `rpy` (roll, pitch, yaw) and `quat` |
| `r.state.temps()` | motor temperatures, and the `hottest` one |
| `r.hands.state("right")` | `q` (7 finger angles), `pads` (9 touch pads, names in `pad_names`), `temp` |
| `r.camera.read()` | `(t, picture)`: an array of height × width × 3 colours (needs Pillow). `r.camera.jpeg()` gives the JPEG file instead |
| `r.depth.read()` | `(t, xyz, rgb)`: 3-D points in metres and their colours |
| `r.on("joints", f)` | calls `f(js)` for every new reading, in the background. Also `"imu"`, `"hands.right"`, `"hands.left"`, `"temps"`, `"camera"`, `"depth"`, `"lidar"`, `"head_imu"`, `"tf"`, `"session"`. It returns a function: call it to stop |

A read gives the newest reading. If a sensor has sent nothing for a while,
the read waits up to 2 seconds and then raises `NoData`.

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

`r.control()` first waits for your turn. It prints why it is waiting (*ben
has the robot; you are 1st in line*) and goes on by itself when your turn
comes. It waits 10 minutes at most; `r.control(wait=60)` waits less. Then
the robot eases into its standing pose, which takes a few seconds, and the
block starts.

`c.status` tells you:

- `clamped`: you asked for more than a joint can do; the robot went as far as it is allowed;
- `held`: the arms stopped part way, because going on would hit something;
- `resting`: an arm was up too long and is resting by its side, for the seconds shown;
- `refused`: the last pose was refused, and why. It goes back to None when a pose is taken again.
  The arms hold the last safe pose, and a `move_to` or `home()` after a refused `set` starts from there.

## Recording a dataset

`g1lab.Recorder` writes the sensors to a folder, and `g1lab.Recording` reads
them back, all on one clock. It needs no session and the robot does not move.
The computer running your program must stay on the Robot Network, and the
recording lands on that computer.

```python
import g1lab

run = g1lab.Recorder("192.168.123.222", "hallway").run(seconds=30)   # or "mock"
print(run)                                     # what it holds, per sensor
for t, lidar in run.read("lidar"):
    joints = run.at("joints", t, max_age=0.1)  # (time, joints) at that moment
```

To record while your program does something else, use `with
g1lab.Recorder(...):` around that code. To read a folder later,
`g1lab.Recording("hallway")`.

From a terminal: `python -m g1lab.record --host 192.168.123.222 --seconds 60
--out hallway`, then `python -m g1lab.record show hallway`.

| Call | What you get |
|---|---|
| `Recorder(source, out, topics)` | `source` is the robot computer's address, or a connected robot or mock. `out` is a new folder (default `recording_<date>_<time>`). `topics` narrows what is kept; the default is everything but depth, and `g1lab.recording.ALL_TOPICS` adds it. It stops by itself with less than 1 GB left on the disk |
| `rec.run(seconds)`, `rec.start()`, `rec.stop()`, `rec.counts()` | record for that long (until Ctrl-C with no number); start and stop in the background (`stop()` and `run()` return the Recording); readings so far, per sensor |
| `run.read(topic, start, end)` | every reading in that time span as `(t, value)` |
| `run.at(topic, t, max_age)` | the newest reading at or before `t` as `(t, value)`, `None` if none is that recent |
| `run.play(topics, start, end)` | `(t, topic, value)` across sensors, in time order |
| `run.stamps(topic)` | all of a sensor's times, as an array |
| `run.topics`, `run.t0`, `run.t1`, `run.duration`, `run.summary()` | what the folder holds |

A camera value is the picture, a depth value is `(xyz, rgb)`, and every other
value is the same dictionary the stream carries. Pass `raw=True` to get the
stored message instead, untouched.

**Size:** about 1.5 MB a second, so a minute is about 90 MB. Depth adds about
0.9 MB a second. **The clock:** every `t` is the robot computer's clock. Camera
pictures are stamped about 50 ms before they arrived, when the robot took them.

## When something goes wrong

Each problem is its own exception, so you can catch the one you expect:

| Exception | What it means | What to do |
|---|---|---|
| `Disconnected` | no answer from the robot computer | check the address (in the lab: `192.168.123.222`) |
| `NoSession` | the robot computer answers, but no session is running | the operator starts one; `control()` waits for it |
| `Busy` | someone else has the robot (`e.owner`, your place `e.place`) | `control()` waits your turn; this comes only when `wait` runs out |
| `NameInUse` | someone on another computer uses your name | pick another `name` |
| `Refused` | the pose would hit the robot itself (`e.reason` says what) | change that arm's angles. `move_to` raises it; after `set` it shows on `c.status.refused` |
| `Ended` | the session is over, or ending | stop; your program is done |
| `NoData` | a sensor sent nothing | that sensor is off, or the session does not carry it |
| `ServiceRefused` | `r.services.start()` may not start that service (`e` says why) | read the reason; the operator starts robot services |

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
r.services.start("sim", wait=120)    # a simulated robot for your program; tens of seconds
with r.control() as c:               # then use it as usual
    ...
r.services.start("llm", wait=120)    # the language model on the robot computer
print(r.services.status("llm"))      # ServiceInfo(name='llm', state='running', programs=1, ...)
r.services.stop("llm")               # you are done with it
print(r.services.status())           # every service: what it is, and whether it runs
```

- **sim** is a simulator session that only ever drives the simulated robot.
  Only one runs at a time, and never while the real robot is on.
- **llm** is the language model (it answers on port 8080 of the robot
  computer, for programs running there). It needs about 22.5 GB of the
  graphics card, and the robot's controller must always keep 2 GB, so it is
  refused when the card is too full (the reason gives the numbers), and
  while the real robot is running, since it would slow the robot's controller.
- **deploy, session** move the robot. Only the
  operator starts them, from the launcher; `start()` raises
  `g1lab.ServiceRefused` saying so.
- **vision, speech, recorder** are planned: `start()` says "not available yet".
  Recording already works from your own program; see
  [Recording a dataset](#recording-a-dataset). The `recorder` service would run
  it on the robot computer instead.

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
refuses is refused here too, with the same words. Every example takes
`--host mock`. Needs MuJoCo (`pip install mujoco`).

```python
r = g1lab.mock(name="YOURNAME", view=True)  # view: a 3-D window with the robot's pose
with r.control() as c:
    c.arms.move_to(right=..., duration=2.0)
```

What it is not: the legs stand still, nothing balances or heats up, the hand
pads read zero, and the camera plays a short recorded clip (or nothing).
`g1lab.mock(camera="render")` draws the head camera's view instead: the
mock robot's own arms and a red ball in front of the right shoulder
(`ball=(x, y, z)` moves it, `ball=None` removes it; needs Pillow). The
simulated camera sits where the robot's camera sits, with the same lens, so
pixel maths that works here works on the robot.
Joints follow the command about 0.1 s behind, as on the robot. The session
runs like a real one: settling for 2 s after your first pose, then live, and
after `minutes=` (45) the arms go home and it ends. `say=print` shows the
robot computer's own messages ("pose held: ...", "arm resting"). On a Mac,
run a program with `view=True` using `mjpython` instead of `python`.

### The robot's lidar (not open yet)

The real robot has a 3-D lidar on its head. Once it is switched on in the
lab, these calls read it, with no session, like the camera:

| Call | What you get |
|---|---|
| `r.lidar.read()` | a `Cloud`: `xyz` (up to 4,000 points, metres, in the lidar's frame `livox_frame`), `intensity` (0 to 255), `t`. 10 times a second. `cloud.points()` gives the `xyz` |
| `r.lidar.imu()` | the lidar's own motion sensor: `gyro` (rad/s) and `acc` (m/s², gravity included), several samples per reading with their times in `stamp`. The gyro reads about 0.06 rad/s (3°/s) when the robot is still: average it for a second or two at rest and subtract that before adding up turns |
| `r.state.tf()` | where each part of the robot is relative to the next (`transforms`: `parent`, `child`, `xyz`, `quat` as w, x, y, z), for turning lidar points into the body's frame |

The points are thinned to about one per 4 in cube, so a reading is light
enough for Wi-Fi.

## Example programs

In [examples/](../examples/) (run them with `--host` and `--name`):

| File | What it does |
|---|---|
| `info.py` | checks you can reach the robot; prints the joints, limits and home |
| `wave.py` | waves the right arm and opens and closes the hand; change `pose_at` for your own motion |
| `raise_arm.py` | raises the right arm, holds it, lets go |
| `sensors.py` | reads the joints, tilt, hand pads, temperatures and one camera picture |
| `record_dataset.py` | records all the sensors to a folder, then lines each lidar reading up with the joints at that moment |
| `record_camera.py` | records the head camera to numbered JPEGs (and an MP4 with `--video`) for a dataset; see [lab/camera_quickstart.md](camera_quickstart.md) |

## Modules

[notebooks/](../notebooks/) holds worked notebooks that show how to use each
feature. All their code runs from top to bottom, on the mock first:
Joints and frames, Trajectories, Inverse kinematics, Perception (find the red
ball, point at it), Camera and depth, Recording a dataset, Services and the
language model, Refusals and errors. Its
[README](../notebooks/README.md) says what to install.
