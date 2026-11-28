# Changes

What each release added or fixed. To get the newest, run the install line in the
[README](README.md) again.

## 0.1.20 (2026-11-27)

Changed
- `r.info()` says what is on. `r.info().robot` is `"off"`, `"sim"` or `"robot"`, and
  `r.info().features` has one entry for each of `arms`, `walking`, `camera`,
  `policy_trial` and `teleop`, each with `.on` and `.why`. When a feature is off, `.why` is one
  sentence saying why and what turns it on. `print(r.info().features)` lists them all. A feature
  the robot computer cannot tell is left out, not guessed. `r.info().owner` and
  `r.info().time_left` are there too, so `r.session()` is no longer needed.
- Refusals say which feature is off and what turns it on, for example "walking is off: the arm
  simulator is on, and it cannot walk" with the two `r.services` calls that switch simulators.
  The robot being off reads "the robot is off", with how to turn on the arm simulator.
- The error for "the robot is off, or this feature is off" is now `g1lab.Off`, with `.feature`
  set to `"walking"`, `"arms"` and so on, or `None` when the whole robot is off. Catch `Off` where
  you caught `NoSession` (the old name still works for now). A `walk()` on the arm simulator, and
  a pose while walking, raise `Off` instead of `Refused`.
- `g1lab.Ended` reads "the robot was turned off, or your control of it ended".
- `python -m g1lab.check` prints a `robot` line and a `features` line.
- The guides, modules and examples describe what is on rather than kinds of run, and the first
  program prints `r.info().features`.

Works with the 0.1.18 and 0.1.19 clients and the older robot computer: a 0.1.20 program
against a robot computer that does not send `features` builds them from what it does send, and
an older program against the new robot computer keeps working.

## 0.1.19 (2026-11-27)

Changed
- `g1lab.connect()` needs no arguments: it connects to the lab workstation as the account you
  are logged in with, and `python -m g1lab.check` and the examples need no `--name` any more.
  There is no waiting line: only one program moves the robot at a time, and a second program's
  motion commands are refused at once with "the robot is in use by ...". `control()` keeps
  trying until the robot is free. Reading the sensors and cameras needs no hold. `Busy` has
  `owner` only, and `info().queue` and the old `r.session().queue` are gone.
- The examples, the modules and the guides all connect to the lab computer at
  `192.168.123.222` and run in the lab simulator; the same program runs on the real robot once
  it is open there. The walking examples start the walking simulator themselves.
- The camera and ZED pages, the ZED examples and the lab-board notes now assume you work on the
  lab workstation, where the camera tools are installed.
- The package is much smaller: about 140 KB in 29 files, down from 15 MB in 114. It has what a
  program needs to talk to the lab computer and run skills, and no longer carries the robot model
  or a stand-in robot. `g1lab.mock()` raises "g1lab.mock() is not part of the installed g1lab
  package"; use `g1lab.connect()`. The `mock` install extra is gone.

Fixed
- A mission step, a program or `c.arms.home()` that ends with `home` now works in the walking
  simulator. It used to end with "arms are still 0.65 rad from home after 3 s". The walking
  simulator now holds the arms at the home pose, so `home`, `c.arms.move_to` and the carrying
  example all behave as they do in the arm simulator.
- Asking for the walking simulator while the arm simulator runs, or the reverse, now says
  which one is running and how to stop it (`r.services.stop("sim")` or `r.services.stop("walk")`),
  as one sentence with no traceback when your program does not catch it; the program still exits
  with an error. The same sentence is the message of the `ServiceRefused` you can catch.
- The Perception module's red ball is in the lab simulator's camera while the robot stands, not
  only before you take control: the closed-loop part now sees it and points at it. The ball is 28 in
  in front of the robot's start spot, 4 in to the right and 39 in above the floor.
- Joints and frames, Inverse kinematics and Perception read the robot's description file from
  the `notebooks` folder (`g1_29dof_dx3_ros.urdf`, now included there) instead of from inside the
  package, so open them with Jupyter started in that folder. Joints and frames checks its
  forward kinematics against MuJoCo using that same file.

Added
- Mission steps that walk can use your own navigation. `Mission.run(r, planner=...)` gives
  `go_to` a planner of your own (start from `g1lab.goto.builtin_planner()` and change `step`);
  `go_to=...` replaces the whole walk. `r.nav.go_to(..., planner=...)` takes the planner too. The
  walk still goes through the robot's safety layer, and a planner that returns NaN or three numbers
  of the wrong shape is refused with a message. Nothing changes if you pass neither. Walking runs
  in the walking simulator only.

Not yet
- `r.vision` (your own detector), the Vision model module, and the mission steps `find`,
  `approach`, `pick` and `place` wait for the lab simulator. Only `go_to` and `home` missions run in the walking simulator so far.

## 0.1.18 (2026-11-24)

Fixed
- The simulated head camera now tilts down like the real one, about 17 degrees below
  horizontal (it was about 47). `g1lab.mock(camera="render")` and the simulator's detector
  both use it, so objects sit where they would in the robot's picture.
- The Perception module's `MOUNT_RPY` holds the real camera's angles, so its `camera_pose`
  and `ball_position` agree with the robot's camera.

Changed
- The mock's red ball moved up into the new view: 18 in in front of the robot, 4 in to its
  right, 41 in above the floor. The Perception and Vision model modules use that position;
  their "Try this" ball is now `ball=(0.50, -0.20, 1.10)`.

## 0.1.17 (2026-11-24)

Fixed
- `r.session().time_left` was `None` on the first call after `connect()`, even while a program
  had the robot. The first call now waits up to 2 s for the robot computer's first update
  and reports the seconds left. It is still `None` before LIVE and when the robot is off.
- `r.info().backend` said `"robot"` when the robot was off, which is not a fact the robot
  computer has. It is `None` until the robot is on, then `"robot"` or `"sim"` (`"mock"` on the mock).
- `pip install "g1lab[vision]"` did not install `onnx`, which the Vision model module needs
  to build its model. The `vision` extra now installs `onnx` and `onnxruntime`.

Docs
- The `r.info()` and `r.session()` rows in the API table say what `backend` and `time_left`
  hold, and the `vision` extra lists both packages.

## 0.1.16 (2026-11-23)

Fixed
- `r.services.start("sim", wait=...)` (and `"walk"`) now returns only when the simulator takes
  programs, so `r.control()` works right after it. It used to return about 30 s before that,
  so a `r.control()` straight after it still had to wait. If `wait` runs out first it raises
  `g1lab.G1LabError`: "the simulator is still starting: wait a little longer, or start with a
  larger wait=".

Added
- `r.policy`: send a policy folder from your own program. `upload(folder)` checks it on the
  robot computer (the policy loads with no network and no home folders) and returns its hash,
  kind, inputs and outputs; `trial()` runs it in the arm simulator and scores it against
  the floor, the minimum scores a trial must reach ([docs/policy.md](docs/policy.md));
  `progress=print` shows each episode as it runs. `status()` and `list()` show the last
  trial and the operator's approval. While the simulator is still starting, `r.policy` says
  so instead of telling you to start one. The arm simulator only: the operator approves a
  passing hash and runs it on the robot with you.

## 0.1.15 (2026-11-23)

Fixed
- The example policy class in the Policy page and in `help(g1lab.policy)` set its state
  only in `reset()`, so a copy of it failed the check before a trial with
  `AttributeError`. It sets its state in `__init__` too, and the page says why.
- The refusal you get from `r.vision` on the robot now says what to do: it is not switched
  on there yet, so test your model on `g1lab.mock(camera="render")`.
- `examples/sensors.py` no longer crashes in a simulator: the simulator's hands
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
  `docs/vision.md`.
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
