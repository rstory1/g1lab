# Policies

A policy is a network or a Python class that drives the arms and hands 50 times a
second. It gets the readings it asks for and answers with joint angles. The robot's
joint limits and collision checks apply to every answer.

You hand the operator a folder, and the operator runs it. There is no way yet to
send one from your own program.

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
`NetworkPolicy` on your laptop with `onnxruntime` installed, but the lab cannot run one
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
`policy.json` of `{"file": "my_policy.py"}`:

```python
import numpy as np
from g1lab.policy import Policy

class Reach(Policy):
    inputs = ("right_arm_q", "right_pads")
    outputs = ("right_arm",)

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

**The simulator has no touch pads yet.** `right_pads` and `left_pads` read zero there and on
the mock, and your trial says so. A policy that depends on touch is not tested by its trial.

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

1. **Simulator trials.** Several episodes, scored against the instructor's floor: how many
   finished, how many answers were late or refused, and the rate. For now, finishing an
   episode counts as success; a test for your task comes with the lab's simulator scene.
2. **The operator's approval.** It is for those exact files. **If you change one byte,
   it is a new policy** and starts again at step 1.
3. **First run on the robot,** standing at the table, at reduced speed, with a spotter.
4. **Full speed,** once that run has gone well and the operator has approved it.

You can make the floor stricter for your own policy, never looser:

```json
{"file": "reach.pt", "inputs": ["right_arm_q"], "outputs": ["right_arm"],
 "floor": {"min_success": 1.0}}
```

The numbers are `min_episodes`, `min_success`, `max_watchdog_trips`, `max_refused_share`,
`max_miss_share` and `min_hz`.

## Trying it without the robot

`g1lab.mock()` gives the same readings, limits and refusals. This runs your class in your own
program, with no sandbox and no 40 ms limit:

```python
import g1lab, time
from g1lab import policy

p = Reach()
p.reset()
with g1lab.mock(name="YOURNAME") as r, r.control() as c:
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
