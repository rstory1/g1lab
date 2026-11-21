# Walking, reaching and missions

Four things your program can do:

1. [Walk to a point: `r.nav.go_to()`](#1-walk-to-a-point-rnavgo_to)
2. [Plan a reach with the arm: `g1lab.reach`](#2-plan-a-reach-with-the-arm-g1labreach)
3. [Missions: skills in a row](#3-missions-skills-in-a-row)
4. [Carry something while walking](#4-carry-something-while-walking)

**Where it runs today.** On your laptop with `g1lab.mock()`, and in the lab in the
**walking simulator** session, which your program starts itself with
`r.services.start("walk")`. Walking on the real robot is not open to programs
yet. Every example below runs on your laptop first, with g1lab installed as in
[the guide](guide.md#install) (its install line has the `mock` and `missions`
extras these need).

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
positive. On the robot the pose is a guess built from its steps: it slowly goes wrong, so
check `pose.quality` (`"ok"` or `"degraded"`) and `pose.drift_m` (estimated error, meters) in long
programs; at 20 in of estimated error it stops coming. To try that on the laptop, use
`g1lab.mock(nav="lab", robot_pose=True)`. `r.nav.map()` gives the map itself. You can also walk by hand with
`c.walk(vx, vy, wz)` (forward, left, turning); each call lasts half a second, so
call it in a loop or pass `duration=`, and `c.stop()` stops at once.

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
        js = r.state.joints()
        waist = [js["waist_yaw"], js["waist_roll"], js["waist_pitch"]]
        plan, miss = solver.refine(plan, js.arm("right"), waist)
        c.arms.move_to(right=plan.grasp, duration=0.5)
r.close()
```

- `plan.pre`, `plan.grasp`: the two arm poses. `plan.approach_name` says how the
  hand comes in (`side`, `top`, ...).
- `solver.refine(plan, measured_angles, measured_waist)`: the arm never lands
  exactly where it was told, and while the robot stands the walking policy turns
  the waist as the arm reaches (in the simulator about 0.17 rad, which moves the hand 8 to 9 cm
  sideways). This looks at where the hand really is, on the measured waist, and
  returns a corrected plan and how far off it was (`miss`, in m). Leave out the
  waist and the solver assumes it is straight.
- `Unreachable`: no arm pose gets there. The message says why: too far from the
  shoulder ("get closer"), or how short the hand comes and which joints are at
  their stops. The arm reaches only about 0.3 to 0.4 m (12 to 16 in) ahead of
  the pelvis, so the robot has to stand close.

Only the **right** hand: asking for the left raises `Unreachable`. The solver only
plans; the robot still checks every pose, so `c.arms.move_to` can raise
`g1lab.Refused` (for example, the hand would hit the body).

## 3. Missions: skills in a row

A mission is a short list of skills (`find`, `go_to`, `approach`, `pick`, `place`,
`drop`, `home`) run one after another, from a YAML file or from Python.
[mission_basic.py](../examples/mission_basic.py) runs
[mission_basic.yaml](../examples/mission_basic.yaml) on the mock, in a pretend
room with a pretend detector. Every skill, every failure code and where missions run:
[Missions: skills in a row](missions.md).

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
- Walking right up to a table: `go_to` keeps about 18 in from furniture.
- The left hand for grasping.
