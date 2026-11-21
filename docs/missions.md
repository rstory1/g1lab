# Missions: skills in a row

A mission is a short list of skills the robot does one after another: look for the casting, walk up
to it, pick it up. You write it as a file or as Python; both run the same way.

**Where it runs.** On your laptop a whole mission runs on the mock, in a pretend room with a
pretend detector (`g1lab.mockworld`, see "Try it"). In the lab, missions run in the walking
simulator (`r.services.start("walk")`), not on the real robot yet. **There is no object detector
in the lab yet**, so there only `go_to` and `home` steps run: `find` stops with `unavailable` and
says so, and `approach` and `pick` need a `find` first. Walking and reaching on their own:
[walk_reach_missions.md](walk_reach_missions.md).

## A mission file

```yaml
mission: fetch_casting
timeout: 240                    # seconds for the whole mission (optional)
params: {label: casting}        # ${label} below; override: --param label=bolt
steps:
  - find: {label: "${label}", scan: true}          # turn in place until the detector sees it
  - approach: {target: "${label}", standoff: 0.3}  # walk to 0.3 m from it, facing it
  - pick: {target: "${label}"}                     # reach, grasp, lift
  - home                                           # arms back to home
```

Check it before anything moves, and run it:

    python -m g1lab.mission check fetch.yaml
    python -m g1lab.mission steps fetch.yaml           # every step with its defaults filled in
    python -m g1lab.mission run fetch.yaml --host 192.168.123.222 --name YOURNAME   # in the lab; on a laptop see "Try it"

Reading a YAML file needs the `missions` extra (PyYAML), which the README's install line has. A file
written as JSON works without it.

## The same thing in Python

```python
from g1lab.mission import Mission

m = (Mission("fetch_casting", timeout=240)
     .find("casting", scan=True)
     .approach("casting", standoff=0.3)
     .pick("casting")
     .home())
result = m.run(r)                       # r = g1lab.connect(...) or g1lab.mock()
print(result.status, result.failed_step, result.message)
```

`Mission.load("fetch.yaml")` loads a file into the same object, so you can start from a file and add steps in code.

## The skills

| Skill | What it does | Main arguments |
|---|---|---|
| `find` | looks for a label in your detector's output and remembers where it is | `label`, `timeout` 10, `min_conf` 0.5, `scan` (turn while looking) |
| `go_to` | walks to a point on the map | `x`, `y`, `yaw`, `tolerance` 0.15, `timeout` 60 |
| `approach` | walks to `standoff` m in front of something `find` saw, then looks again to check | `target`, `standoff` 0.5 |
| `pick` | reaches the target, closes the hand, lifts; checks the touch pads | `target`, `hand` (auto, left, right), `verify` (pads, none) |
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

## Try it

[examples/mission_basic.py](../examples/mission_basic.py) runs `mission_basic.yaml` (find a cup, walk up to it, pick it up) on
the mock with a made-up floor and detector (`g1lab.mockworld`), so you see the steps work. The mock's
touch pads read nothing, so the example passes `verify: none`; on the robot leave it on `pads`.

