# Policies

A policy is a network or a Python class that drives the arms and hands 50 times a
second. It gets the readings it asks for and answers with joint angles. The robot's
joint limits and collision checks apply to every answer.

You send a folder from your own program and trial it in the simulator; the operator
approves a passing policy and runs it on the robot with you.

## Send it and trial it

This needs the arm simulator (`r.services.start("sim", wait=120)`, which returns once the
simulator takes programs; before that, `r.policy` says the simulator is still starting). Give up the robot
before a trial (no `r.control()` open in any program of yours): the trial drives the
simulated arms.

```python
import g1lab

with g1lab.connect() as r:
    info = r.policy.upload("reach")             # the folder with policy.json
    print(info.hash[:12], info.kind, info.inputs, "->", info.outputs)

    result = r.policy.trial(info, progress=print)   # 5 episodes, scored against the floor
    print(result)                               # passed or under the floor, and why
    print(r.policy.status(info).approved)       # None until the operator approves it
```

`upload` sends the folder's files (up to 100 files and 64 MB; `__pycache__` is left out),
and the robot computer loads the policy in the same sandbox the operator's check uses: no
network, no home folders. It returns when the check is done. `info.hash` names these exact
files: tell the operator the hash, and the operator approves that hash. A changed byte is a
new hash and starts again.

`trial` returns a `TrialResult`: `passed`, `why` (each number that missed the floor, the minimum scores a trial must reach),
and `episodes`, `success`, `watchdog_trips`, `refused_share`, `miss_share` and `hz`.
`progress` gets each line the trial prints, such as `episode 2/5: ran to the end`.
`r.policy.status(hash)` shows the last trial and the approval; `r.policy.list()` lists the
policies you sent.

Refusals come as `ServiceRefused` with the reason:

| Says | Fix |
|---|---|
| `policy trials are off: ... this is not the simulator` | `r.services.start("sim", wait=120)` |
| `no policy.json` | add it ([below](#a-network-no-code)) |
| `is a link` | a folder holds real files, not links |
| `over 64 MB`, `the most is 100` | leave out data and checkpoints the policy does not load |
| `failed its check` | the message holds the policy's error and what it printed |
| `a trial is already running` | trials run one at a time; wait for it |
| `already have 20 policies` | you can keep 20 and no call removes one: `r.policy.list()` shows them; trial one of those |

A policy belongs to the login account you run under: use the same account each run to trial it
again without uploading, because another account cannot see it. Approving a policy and running it on the
robot are not in `r.policy`: those are the operator's.

## A network: no code

Put your exported network in a folder with a `policy.json`:

```json
{
  "file": "reach.pt",
  "inputs": ["right_arm_q", "right_pads"],
  "outputs": ["right_arm"]
}
```

`file` is a TorchScript file (`.pt`, `.ts`). An ONNX file (`.onnx`) loads in
`NetworkPolicy` in your own account with `onnxruntime` installed, but the lab cannot run one
yet, so export TorchScript for the lab. A checkpoint of
weights alone has no network in it, so export it first, or load it from a class (below):

```python
torch.jit.script(net).save("reach.pt")
```

- **Input:** every input in the order you listed them, flattened into one float32
  vector of shape `(batch, n)`. Here that is 7 + 9 = 16 numbers.
- **Output:** one array of shape `(batch, 7 x outputs)`, split in the order you listed
  them. The values are absolute target angles in radians.
- **Normalising:** do it inside the exported network. Nothing scales your inputs.
- **Images or several inputs:** set `"concat": false`. The network then takes one tensor
  per input, in the order you listed them, with `head_image` as float32 NCHW in 0..1.

## A Python class

Use one when you need your own logic around a network. The folder holds your file and a
`policy.json` of `{"file": "my_policy.py"}`. Set up what `act()` needs in `__init__`,
because the check before a trial calls `act()` before the first `reset()`:


```python
import numpy as np
from g1lab.policy import Policy

class Reach(Policy):
    inputs = ("right_arm_q", "right_pads")
    outputs = ("right_arm",)

    def __init__(self):
        self.start = None

    def reset(self):
        self.start = None               # a new episode

    def act(self, obs_batch):
        q = obs_batch["right_arm_q"]    # shape (1, 7)
        if self.start is None:
            self.start = q.copy()
        target = self.start.copy()
        target[0, 0] -= 0.3             # shoulder pitch: the arm forward
        return {"right_arm": target}
```

To run slower than 50 times a second, set `hz` on the class, or `"hz"` in a network's
`policy.json`. If your file defines several `Policy` classes, name yours with `"class"`.

Your folder can hold other files too, and your class can import them. `print()` goes to a
log the operator can read.

A checkpoint of weights works this way, with no export. Keep the file that builds your
network and the weights in the folder, and load them in `__init__`:

```python
import os
import torch
from g1lab.policy import Policy
from my_net import Net                  # my_net.py, in this folder

class Reach(Policy):
    inputs = ("right_arm_q",)
    outputs = ("right_arm",)

    def __init__(self):
        self.net = Net()
        here = os.path.dirname(__file__)
        self.net.load_state_dict(torch.load(os.path.join(here, "weights.pth"), weights_only=True))
        self.net.eval()

    def act(self, obs_batch):
        with torch.no_grad():
            x = torch.from_numpy(obs_batch["right_arm_q"]).float()
            return {"right_arm": self.net(x).numpy()}
```

Your code has no network and cannot see anyone's files but its own folder, which it can
only read. It can write to `/tmp`, which starts empty and is gone when the run ends. It
runs on the CPU, with the packages already installed there: numpy and torch.

## Inputs

Each has one more leading dimension when it reaches `act()`, the batch.

| Name | Shape | What |
|---|---|---|
| `right_arm_q`, `left_arm_q` | 7 | arm angles, rad: shoulder pitch, roll, yaw, elbow, wrist roll, pitch, yaw |
| `right_arm_target`, `left_arm_target` | 7 | what the controller is being asked for |
| `waist_q` | 3 | yaw, roll, pitch, rad |
| `right_hand_q`, `left_hand_q` | 7 | finger angles, rad: thumb 0, 1, 2, middle 0, 1, index 0, 1 |
| `right_hand_target`, `left_hand_target` | 7 | what the fingers are being asked for |
| `right_pads`, `left_pads` | 9 | the touch pads: thumb, index, middle; tip, mid, base of each |
| `right_grip`, `left_grip` | 7 | hand target minus hand angle: a finger held back by something shows here |
| `imu_rpy` | 3 | body roll, pitch, yaw, rad |
| `imu_quat` | 4 | body orientation, w, x, y, z |
| `time` | 1 | seconds since this episode began |
| `head_image` | h, w, 3 | the head camera, RGB uint8, slower than the rest |

The names are the same in the simulator and on the robot. A policy that asks for an input
this robot does not have is refused before anything moves.

**The simulator has no touch pads yet.** `right_pads` and `left_pads` read zero there,
and your trial says so. A policy that depends on touch is not tested by its trial.

## Outputs

`right_arm`, `left_arm`, `right_hand` and `left_hand`, 7 absolute angles each, in the order
of the table above. Declare only what you drive. What you do not declare stays where it is.

## 40 milliseconds

Each answer must come within 40 ms, or it is thrown away, because the reading it was made
from is old. The arms and hands hold the last answer until a new one comes.

**After 0.5 s with no usable answer, the arms go home and the run ends as a failure.** The
hands stay as they are, so they do not drop what they hold. Each of these counts as no answer:

- an exception in `act()`, or your process ending
- an answer with a value that is not finite, or with the wrong shape
- a pose the robot refuses

A short gap carries on, and the run counts it. A pose outside a joint's limits is moved
inside them and counted as `clamped`.

## From your folder to the robot

1. **Simulator trials** (`r.policy.trial`). Several episodes, scored against the floor, the minimum scores a trial must reach: how many
   finished, how many answers were late or refused, and the rate. For now, an
   episode counts as a success when it runs to the end without getting stuck on a late
   answer. The trial does not check your task itself.
2. **The operator's approval.** It is for those exact files. **If you change one byte,
   it is a new policy** and starts again at step 1.
3. **First run on the robot,** standing at the table, at reduced speed, with a spotter.
4. **Full speed,** once that run has gone well and the operator has approved it.

You can make the floor stricter for your own policy, never looser:

```json
{"file": "reach.pt", "inputs": ["right_arm_q"], "outputs": ["right_arm"],
 "floor": {"min_success": 1.0}}
```

The numbers, with the floor's values for now (the operator may change them):

| Number | Floor | Means |
|---|---|---|
| `min_episodes` | 5 | episodes in one trial |
| `min_success` | 0.8 | share of episodes that succeeded |
| `max_watchdog_trips` | 0 | episodes that ended with no output for 0.5 s |
| `max_refused_share` | 0.02 | share of outputs the joint checks refused |
| `max_miss_share` | 0.05 | share of requests answered later than 40 ms |
| `min_hz` | 40 | outputs a second, averaged over the trial |

## Trying it in your own program

Connected to the lab simulator, your program gets the same readings, limits and refusals as the
trial. This runs your class in your own program, with no sandbox and no 40 ms limit:

```python
import g1lab, time
from g1lab import policy

p = Reach()
p.reset()
with g1lab.connect() as r:
    r.services.start("sim", wait=120)
    with r.control() as c:
        t0 = time.monotonic()
        while time.monotonic() - t0 < 5:
            t = time.monotonic() - t0
            obs = policy.observe(r, p.inputs, t=t, timeout=1.0)
            action = policy.check_action(p.act(policy.batch(obs)), p.outputs)
            c.arms.set(right=action["right_arm"])
            time.sleep(1 / 50)
```

`NetworkPolicy` loads the same files outside a folder, so you can test a network first:

```python
net = policy.NetworkPolicy("reach.pt", p.inputs, p.outputs)
```
