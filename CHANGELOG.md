# Changes

What each release added or fixed. To get the newest, run the install line in the
[README](README.md) again.

## 0.1.16 (2026-11-23)

Fixed
- `r.services.start("sim", wait=...)` (and `"walk"`) now returns only when the session takes
  programs, so `r.control()` works right after it. It used to return about 30 s before that,
  so a `r.control()` straight after it still had to wait. If `wait` runs out first it raises
  `g1lab.G1LabError`: "the simulator is still starting: wait a little longer, or start with a
  larger wait=".

Added
- `r.policy`: send a policy folder from your own program. `upload(folder)` checks it on the
  robot computer (the policy loads with no network and no home folders) and returns its hash,
  kind, inputs and outputs; `trial()` runs it in a simulator session and scores it against
  the floor, the minimum scores a trial must reach ([docs/policy.md](docs/policy.md));
  `progress=print` shows each episode as it runs. `status()` and `list()` show the last
  trial and the operator's approval. While the simulator is still starting, `r.policy` says
  so instead of telling you to start one. Simulator sessions only: the operator approves a
  passing hash and runs it on the robot with you.

## 0.1.15 (2026-11-23)

Fixed
- The example policy class in the Policy page and in `help(g1lab.policy)` set its state
  only in `reset()`, so a copy of it failed the check before a trial with
  `AttributeError`. It sets its state in `__init__` too, and the page says why.
- The refusal you get from `r.vision` on the robot now says what to do: it is not switched
  on there yet, so test your model on `g1lab.mock(camera="render")`.
- `examples/sensors.py` no longer crashes in a simulator session: the simulator's hands
  have no pads (`hand.pads` is `None` there), and it says so.
- `examples/go_to_basic.py` prints the straight-line distance to the goal, which is what
  "arrived within 0.15 m" measures; `h.remaining_m` is along the planned path and can read more.
- `python -m g1lab.check` with a name already in use says to pick another `--name` or wait
  10 s, instead of pointing at the address.
- The Trajectories module waits for a resting arm to finish resting before it measures.
- The refusal from `record_camera.py`, `zed_easy.py` and `zed_sdk.py` for a missing OpenCV or
  Pillow no longer says to `pip install` from the Robot Network, which has no internet.

Docs
- The Record a dataset example reads the camera, which runs on the robot today, not the
  lidar, which does not yet.
- The `NoSession` fix is `r.services.start("sim", wait=120)` or waiting; "no answer" means
  a wrong address or that the robot computer is not running.
- The vision page and module open with where it runs today (the mock), say plainly that
  the mock's depth is used only inside `r.vision`, and no longer name the robot's internals.
- The guide opens by saying what runs only on the simulated robot (moving the arms), and the
  `ServiceRefused` row gives a fix for each cause.
- The raw-message page shows the timeout a program really gets (`zmq.error.Again`) and says to
  make a new socket after it.
- The missions page says `mission run` does not start the walking simulator, and how to.
- The mock world's help gives one table height (+0.1 m in the pelvis frame for a 36 in table).
- The policy page lists the floor's values; the vision page's example comment puts `resize`
  inside `input`; the ZED SDK page says how to get the calibration on the Robot Network.
- Logging in to the robot computer for the ZED SDK: at its own desk, with your own
  university account.
- `help()` text for `g1lab.reach`, `g1lab.mock`, `g1lab.vision` and the simulated detector no
  longer names lab scripts, runs or modules; `NoSession` and `Disconnected` say what to
  do. `help(g1lab.vision)` says where it runs today. The ZED
  service is "usually a few seconds, up to a minute the first time" everywhere.

## 0.1.14 (2026-11-22)

New
- `r.vision`: upload your own ONNX detector and read what it finds, each thing with a 3-D
  point. It runs on `g1lab.mock()` now, on your computer, through the robot's own manifest and
  upload checks; the robot's 100 ms per-frame limit is applied only when you upload to the
  robot. Add `vision` to the extras in the install line. With `camera="render"` the mock
  gives each detection a 3-D point from the render's depth (`r.depth.read()` still raises
  `NoData` on the mock). On the robot it is not switched on yet:
  [docs/vision.md](docs/vision.md).
- The Vision model module (`notebooks/vision_model.ipynb`): a model small enough to read,
  with a post.py; a YOLO export from Ultralytics; two models at once; a refused upload.

Fixed
- A program on `g1lab.mock(camera="render")` that ends without `r.close()` no longer
  crashes as it exits (it did about one run in three).

## 0.1.13 (2026-11-21)

Fixed
- A YAML mission file without PyYAML says to add `missions` to the extras in the
  install line, instead of a pip line that installs nothing.
- A service that fails while starting says so in one plain line.
- A `find` step in the lab says plainly that there is no object detector there yet.
- `examples/info.py` marks a joint that cannot move as fixed (the right hand's middle_0).
- `examples/go_to_basic.py` says what counts as arrived (within 0.15 m).
- `examples/record_camera.py` prints one line a second when its output goes to a file.

Docs
- `missions` is in the README's install line; every extra is listed once, in the
  guide's Install section. Lidar, pose, odometry, recordings and walking calls
  are documented where students look for them; fixes throughout.

## 0.1.12 (2026-11-21)

New
- `g1lab.mock(robot_pose=True)`: the mock reports the robot's pose on the map, as the
  robot does, and says why when it has none.
- `python -m g1lab.record --host mock` records the mock's joints.

Fixed
- `g1lab.Recorder("mock")` is refused with a message instead of saving an empty
  recording. Pass `g1lab.mock()` instead.
- `python -m g1lab.export` stops on a damaged recording, and its refusals are one line
  instead of a traceback.
- Walking stops if the robot's position reads as not-a-number.
- `reach` solves the arm with the waist where it really is.

## 0.1.11 (2026-11-17)

- Docs: install pyzed and use the ZED SDK from your own account, no admin needed.

## 0.1.10 (2026-11-17)

Fixed
- `examples/carry_while_walking.py` prints plain numbers.

## 0.1.9 (2026-11-17)

New
- Walking in the walking simulator (`r.services.start("walk")`) and on the walking
  mock: `c.walk()`, and `r.nav.go_to()` to walk to a point on the map.
- Carrying while walking: the arms and hands are yours in the walking simulator, and
  on the mock with `g1lab.mock(nav="lab", arms=True)`.
- Reaching: `g1lab.reach` solves an arm pose that puts the right hand on a target.
- Missions: a list of steps (find, go_to, approach, pick, place, drop, home) in Python
  or a YAML file, checked and run with `python -m g1lab.mission`. On the mock they run
  in a pretend room with a pretend detector (`g1lab.mockworld`).
- Four examples: `go_to_basic.py`, `reach_basic.py`, `mission_basic.py` and
  `carry_while_walking.py`.

## 0.1.8 (2026-11-16)

New
- `python -m g1lab.check`: checks your install and your connection to the robot.

## 0.1.7 (2026-11-16)

New
- The ZED camera's depth image, detected objects, people and the camera's pose.
- Two ZED examples: `zed_easy.py` and `zed_sdk.py` (the SDK yourself).

## 0.1.6 (2026-11-06)

New
- `python -m g1lab.export`: recordings to a LeRobot dataset.
- Policies: write a policy with `g1lab.policy` and try it on the mock.

## 0.1.5 (2026-11-04)

Fixed
- `move_to` after a refused `set` starts from the last pose that was accepted.

## 0.1.4 (2026-11-04)

New
- `r.ask()`: ask the language model a question.

## 0.1.3 (2026-11-04)

New
- The dataset recorder, `g1lab.Recorder`.
- The camera's real lens numbers.

## 0.1.2 (2026-11-03)

- Examples and docs use `--name YOURNAME`, and each example says what it does.

## 0.1.1 (2026-11-03)

- OpenCV moved to the optional `video` extra; the docs say what needs it.

## 0.1.0 (2026-11-03)

First release: connect, read the robot, take control, named errors, and the mock.
