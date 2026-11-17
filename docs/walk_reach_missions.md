# Walking, reaching and missions

New in g1lab 0.1.9. Four things your program can now do:

1. [Walk to a point: `r.nav.go_to()`](#1-walk-to-a-point-rnavgo_to)
2. [Plan a reach with the arm: `g1lab.reach`](#2-plan-a-reach-with-the-arm-g1labreach)
3. [Missions: skills in a row](#3-missions-skills-in-a-row)
4. [Carry something while walking](#4-carry-something-while-walking)

**Where it runs today.** On your laptop with `g1lab.mock()`, and in the lab in the
**walking simulator** session, which your program starts itself with
`r.services.start("walk")`. Walking on the real robot is not open to programs
yet. Every example below runs on your laptop first:

```
pip install "g1lab[mock,missions] @ https://github.com/rstory1/g1lab/releases/download/v0.1.10/g1lab-0.1.10-py3-none-any.whl"
```

## Before you start: the walking session

A walking session is like the arm session you already know, plus walking.
You still take your turn with `with r.control() as c:`.

```python
import g1lab

r = g1lab.mock(name="YOURNAME", nav="lab")    # laptop: a pretend 8 x 6 m room
# in the lab:
#   r = g1lab.connect("192.168.123.222", name="YOURNAME")
#   r.services.start("walk", wait=300)        # about a minute to start
print(r.nav.pose())                           # where the robot is on the map
r.close()
```

`r.nav.pose()` gives the robot's place on the map: `x`, `y` in meters and `yaw`
(which way it faces) in radians, 0 along the map's x axis and counterclockwise
positive. `r.nav.map()` gives the map itself. You can also walk by hand with
`c.walk(vx, vy, wz)` (forward, left, turning); each call lasts half a second, so
call it in a loop or pass `duration=`.

**Safety: the robot's limits always win.** Every step goes through the same
safety layer the operator sets up, and your program cannot loosen it: at most
0.3 m/s (1 ft/s) forward, slowing near obstacles and stopping about 0.6 m (2 ft)
from one, and stopping within half a second if your program goes quiet. It
also takes a moment to stop, so leave room. The simulated robot starts late and
walks slower than you ask: read what it really does from `c.status.delivered`.

## 1. Walk to a point: `r.nav.go_to()`

`go_to` plans a route around the walls, walks it, and steers around new
obstacles it sees. Example: [go_to_basic.py](../examples/go_to_basic.py).

```python
import math
import g1lab

r = g1lab.mock(name="YOURNAME", nav="lab")
p = r.nav.pose()
with r.control() as c:
    h = r.nav.go_to(p.x + 1.0, p.y, yaw=0.0)     # 1 m along the map's x axis; waits until done
print(h.result, h.reason)                        # arrived None
print(h.pose, round(h.remaining_m, 2))           # where it stopped, how far from the goal
r.close()
```

What `h.result` means:

| Result | What happened | What to try |
|---|---|---|
| `"arrived"` | it got within `tolerance` (0.15 m) of the goal | |
| `"no_path"` | no route on the map, before it moved | the goal is in or near a wall: `go_to` keeps the robot about 18 in from walls and furniture. Pick a goal further out |
| `"blocked"` | a route closed while walking, or it stopped making headway | clear the way, or pick another goal |
| `"stopped"` | the safety layer held it still, your turn ended, or the robot's position stopped coming | read `h.reason` |
| `"timeout"`, `"cancelled"` | out of time (`timeout=60`), or you called `h.cancel()` | |

`h.reason` explains any result but `"arrived"`, in words. Every ending stops
the robot. `go_to(..., wait=False)` returns at once so your program can do
something else, then `h.wait()`; `on_progress=f` calls `f(h)` a few times a
second. Do not call `c.walk()` yourself while a `go_to` runs.

## 2. Plan a reach with the arm: `g1lab.reach`

`ReachSolver` turns a point in front of the robot into the seven right-arm angles
that put the **grasp center** of the hand on it (the spot between the fingers
where a small object should be, not the wrist). It gives two poses: the **pre-grasp**, 10 cm
(4 in) back, and the **grasp**. Example: [reach_basic.py](../examples/reach_basic.py).

```python
import g1lab
from g1lab.reach import ReachSolver, Unreachable

r = g1lab.mock(name="YOURNAME")
solver = ReachSolver.from_info(r.info())          # this robot's own joint limits
try:
    plan = solver.plan("right", (0.35, -0.15, 0.05))   # x forward, y left, z up from the pelvis (m)
except Unreachable as exc:
    print("cannot reach:", exc)
else:
    with r.control() as c:
        c.arms.move_to(right=plan.pre, duration=2.0)
        c.arms.move_to(right=plan.grasp, duration=1.5)
        plan, miss = solver.refine(plan, r.state.joints().arm("right"))
        c.arms.move_to(right=plan.grasp, duration=0.5)
r.close()
```

- `plan.pre`, `plan.grasp`: the two arm poses. `plan.approach_name` says how the
  hand comes in (`side`, `top`, ...).
- `solver.refine(plan, measured_angles)`: the arm never lands exactly where it was
  told. This looks at where the hand really is and returns a corrected plan and
  how far off it was (`miss`, in m).
- `Unreachable`: no arm pose gets there. The message says why: too far from the
  shoulder ("get closer"), or how short the hand comes and which joints are at
  their stops. The arm reaches only about 0.3 to 0.4 m (12 to 16 in) ahead of
  the pelvis, so the robot has to stand close.

Only the **right** hand: asking for the left raises `Unreachable`. The solver only
plans; the robot still checks every pose, so `c.arms.move_to` can raise
`g1lab.Refused` (for example, the hand would hit the body).

## 3. Missions: skills in a row

A mission is a short list of skills run one after another: look for an object,
walk up to it, pick it up. Write it as a YAML file or in Python; both run the
same way. The skills are `find`, `go_to`, `approach`, `pick`, `place`, `drop` and
`home`. Example: [mission_basic.yaml](../examples/mission_basic.yaml) and
[mission_basic.py](../examples/mission_basic.py), which runs it in a
pretend room with a pretend detector (`g1lab.mockworld`).

```yaml
mission: fetch_cup
steps:
  - find: {label: cup, scan: true}          # turn in place until it is seen
  - approach: {target: cup, standoff: 0.3}  # walk to 0.3 m from it, facing it
  - pick: {target: cup, hand: right}        # reach, close the hand, lift
  - home: {hands: keep}                     # arms home, still holding
```

```python
import g1lab
from g1lab.mission import Mission
from g1lab.mockworld import MockWorld

r = g1lab.mock(name="YOURNAME", settle=0.3)
MockWorld(r, objects={"cup": (1.5, 0.4, 0.1)})   # a pretend cup and floor
m = (Mission("fetch_cup", timeout=120).find("cup", scan=True)
     .approach("cup", standoff=0.3).pick("cup", hand="right", verify="none").home(hands="keep"))
result = m.run(r)
print(result.status, result.failed_step, result.message)
r.close()
```

`python -m g1lab.mission check mission_basic.yaml` checks a file before anything
moves (YAML needs the `missions` extra). The mission stops at the first step that
fails: the robot stops, the arms go home, and `result.status` is `failed` with a
`code` in words, such as `not_found`, `no_path`, `unreachable` (stand closer) or
`refused`. Every skill and every code: [Missions: skills in a row](missions.md).

**In the lab today:** object detection is not in this release, so in the walking
simulator a mission can use `go_to` and `home` steps only; a `find` step fails with
`unavailable` and says so. The whole find, approach, pick mission runs on your laptop
on the mock, with `MockWorld` as above.

## 4. Carry something while walking

In the walking simulator the arms and hands are yours too, standing and walking
(`r.info().arms` is True). On the laptop, `g1lab.mock(nav="lab", arms=True)`
does the same. Example: [carry_while_walking.py](../examples/carry_while_walking.py).

```python
import g1lab

r = g1lab.mock(name="YOURNAME", nav="lab", arms=True)
p = r.nav.pose()
with r.control() as c:
    c.arms.move_to(right=[-0.9, 0.1, 0.0, 0.9, 0.0, 0.0, 0.0], duration=3.0)   # arm out
    h = r.nav.go_to(p.x + 1.0, p.y, yaw=0.0)      # the arm stays where you put it
    c.arms.home()
r.close()
```

The arm rules are the arm session's: joint limits, speed limits, and a pose that
would hit the robot is refused. **The arms go home by themselves** when you leave
the `with` block, when the robot falls, when your program goes quiet for a
second, and when the connection drops. They do not go home when the robot only
stops for an obstacle, so you keep what you carry. Raise the arm before you walk,
not while walking: the robot walks less steadily with its arms out.

## Not available yet

- Walking, reaching while walking and missions on the **real robot**. When they
  open, the operator decides when, and a spotter with the emergency stop stands
  by the robot; the operator or spotter can stop your program at any time.
- A detector your program can use in the lab, so `find`, `approach` and `pick`
  run on the laptop only for now.
- Walking right up to a table: `go_to` keeps about 18 in from furniture.
- The left hand for grasping.
- Starting a mission from the lab's launcher: you run it from your own program.
