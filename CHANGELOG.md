# Changes

What each release added or fixed. To get the newest, run the install line in the
[README](README.md) again.

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
