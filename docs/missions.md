# Missions: skills in a row

A mission is a short list of skills the robot does one after another: look for the casting, walk up
to it, pick it up. You write it as a file or as Python; both run the same way.

**Where it runs.** In the lab, missions run in the walking simulator
(`r.services.start("walk")`), not on the real robot yet. **There is no object detector in the
lab yet**, so only `go_to` and `home` steps can run: `find` stops with `unavailable` and says so,
and `approach`, `pick` and `place` need a `find` first. They wait for the lab simulator to
have a detector. `home` works in the walking simulator as it does in the arm simulator: the arms
glide to the home pose when the walking simulator takes your program and stay there until you move them,
and a `home` step puts them back.
Walking and reaching on their own:
[walk_reach_missions.md](walk_reach_missions.md).

## A mission file

```yaml
mission: two_points
timeout: 240                    # seconds for the whole mission (optional)
params: {x: 1.0}                # ${x} below; override: --param x=0.5
steps:
  - go_to: {x: "${x}", y: 0.0, yaw: 0.0}   # walk to a point on the map
  - go_to: {x: 0.0, y: 0.0}                # and back
```

Check it before anything moves, and run it:

    python -m g1lab.mission check two_points.yaml
    python -m g1lab.mission steps two_points.yaml      # every step with its defaults filled in
    python -m g1lab.mission run two_points.yaml --host 192.168.123.222

`mission run` does not start the walking simulator: it connects to one that is already up. In the
lab, start it first (about a minute), then run the mission; the simulator keeps running after this
line ends:

    python -c "import g1lab; g1lab.connect().services.start('walk', wait=300)"

Reading a YAML file needs the `missions` extra (PyYAML), which the README's install line has. A file
written as JSON works without it.

## The same thing in Python

```python
from g1lab.mission import Mission

m = (Mission("two_points", timeout=240)
     .go_to(1.0, 0.0, yaw=0.0)
     .go_to(0.0, 0.0))
result = m.run(r)                       # r = g1lab.connect(...), with the walking simulator started
print(result.status, result.failed_step, result.message)
```

`Mission.load("two_points.yaml")` loads a file into the same object, so you can start from a file and add steps in code.

## The skills

| Skill | What it does | Main arguments |
|---|---|---|
| `find` | looks for a label in your detector's output and remembers where it is | `label`, `timeout` 10, `min_conf` 0.5, `scan` (turn while looking) |
| `go_to` | walks to a point on the map | `x`, `y`, `yaw`, `tolerance` 0.15, `timeout` 60 |
| `approach` | walks to `standoff` m in front of something `find` saw, then looks again to check | `target`, `standoff` 0.5 |
| `pick` | reaches the target, closes the hand, lifts; checks the touch pads after the close and again with the hand lifted | `target`, `hand` (auto, left, right), `verify` (pads, none) |
| `place` | puts the held thing at a point in front of the robot (x forward, y left, z up, m) or at a found target | `x`, `y`, `z` or `target` |
| `drop` | opens the hand where it is | `hand` |
| `home` | both arms home, checked against the joint readings | `hands` (keep, open) |
| `policy` | runs a policy the operator has approved; only when the operator runs the mission (from your own program it stops with `unavailable`) | `name`, `seconds` |

Every skill has a `timeout`. `retries: 1` on a step tries it again after a failure that might go
away (not found, blocked, no grasp), never after a timeout or a refusal.

## When something fails

The mission stops at the first step that fails. The robot holds still, the arms go home, and you get a
result: `status` (`done`, `failed`, `cancelled`, `timeout`, `error`), `failed_step`, and for each step a
`code` and a message in words: `not_found`, `lost_target`, `blocked`, `no_path`, `unreachable` (move
closer: the arm reaches about 0.3 to 0.4 m ahead at table height, the message says how far short and whether a waist lean would help), `no_grasp`, `refused` (the robot refused a pose),
`unavailable` (something it needs is not there, such as a detector), `no_detector` (the detector
stopped sending), `stopped` (the walking safety layer held the robot still, or its position stopped
coming), `policy_failed` (a `policy` step's policy did not succeed), `precondition`
(for example `approach` before any `find`). A closed hand stays closed until your program ends, then it
lets go.

## Watching it

`m.run(r, on_event=print)` gives every event as a dict; the default prints one line each:

    [   9.4s] step 3/4 pick(target=bottle, hand=auto, ...)
    [  15.4s] step 3 pick: ok holding bottle in the right hand (grasp not verified)

`log_path="run.jsonl"` keeps them as JSON lines, and `result.to_dict()` is the whole outcome as data.

## Walk with your own planner, or your own go_to

Every skill that walks (`go_to`, `approach`, `find` with `scan`) goes through `r.nav.go_to`. You can
change how it walks in two ways. The default is unchanged when you pass neither. Walking runs in the
walking simulator only, so this does too.

**Your own planner.** `go_to` still stops by its own rules (arrived, blocked, no path, timeout, cancelled)
and still sends every velocity through the robot's safety layer, which caps speed and acceleration and keeps
the fence and the stop bubble. Your planner only proposes the velocity. Start from the built-in one and
change its `step`:

```python
import types
import numpy as np
import g1lab
from g1lab import goto
from g1lab.mission import Mission

base = goto.builtin_planner()

class SlowWalker(base.LocalPlanner):
    def step(self, x, y, yaw, now):
        vx, vy, wz = super().step(x, y, yaw, now)     # the built-in's choice
        return np.array([min(vx, 0.25), np.clip(vy, -0.25, 0.25), wz])   # yours: walk at most 0.25 m/s

mine = types.SimpleNamespace(Params=base.Params, LocalPlanner=SlowWalker,
                             distance_field=base.distance_field)

r = g1lab.connect()
r.services.start("walk", wait=300)
result = Mission("slow", timeout=240).go_to(1.0, 0.0, yaw=0.0).run(r, planner=mine)
print(result.status, result.message)
r.close()
```

The built-in walks at 0.3 m/s. The walking simulator's controller needs at least 0.2 m/s to walk and 0.2 rad/s
to turn, and stands still for less: a planner that halves the speed makes the robot stand (the `go_to` ends
`blocked`, "no headway"), so cap the speed instead of scaling it far down.

`step(x, y, yaw, now)` is called about 10 times a second. It gets the robot's place on the map (`x`, `y` in
meters, `yaw` in radians, 0 along +x, counterclockwise) and the time in seconds. It returns three numbers in
the robot's own frame: `vx` forward and `vy` left in m/s, `wz` turning left in rad/s. NaN, infinity or
anything that is not three numbers is refused: the `go_to` ends `stopped` with a message that says what your
planner returned, and nothing is sent to the robot. `r.nav.go_to(x, y, planner=mine)` takes the same
planner outside a mission. A planner is a module-like object with `Params`, `LocalPlanner` and
`distance_field`; `help(goto.builtin_planner)` lists exactly what `go_to` reads from each.

**Your own go_to.** To replace the whole thing, pass a function with `r.nav.go_to`'s signature that
returns what it returns (a handle with `.done`, `.result`, `.reason`, `.pose`, `.remaining_m` and
`.cancel()`). The skills call it with `wait=False`. To walk, send velocities with `c.walk(vx, vy, wz)` on the
handle you opened with `with r.control() as c:`, so the safety layer still limits you; pass that `c` to
`run(r, c=c)` so the mission and your function share your one hold on the robot. This one only reports each call and
then hands over to the built-in `r.nav.go_to`:

```python
import g1lab
from g1lab.mission import Mission

r = g1lab.connect()
r.services.start("walk", wait=300)

def my_go_to(x, y, yaw=None, *, tolerance=0.15, timeout=60.0, wait=True, on_progress=None, **kw):
    print("my go_to:", x, y)                          # your planning goes here
    return r.nav.go_to(x, y, yaw, tolerance=tolerance, timeout=timeout, wait=wait,
                       on_progress=on_progress, **kw)  # then walk, here with the built-in

with r.control() as c:
    result = Mission("mine").go_to(1.0, 0.0).run(r, c=c, go_to=my_go_to)
print(result.status)
r.close()
```

With `go_to=` set, `planner=` is not used.

## Try it

Start the walking simulator, then run the two-point mission above from a program:

```python
import g1lab
from g1lab.mission import Mission

r = g1lab.connect()
r.services.start("walk", wait=300)      # about a minute to start
m = Mission("two_points", timeout=240).go_to(1.0, 0.0, yaw=0.0).go_to(0.0, 0.0)
result = m.run(r)
print(result.status)                    # done, failed, cancelled, timeout, error
r.close()
```

