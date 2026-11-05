# Modules

Each module is a worked notebook that shows how to use one feature. All the code is there
and runs from top to bottom, so read it, run it, and copy what you need.

**Features**

| Module | What it shows |
|---|---|
| `camera_and_depth.ipynb` | read and save pictures, get every new one, read depth, line a depth point up with a pixel |
| `recording_a_dataset.ipynb` | record the sensors to a folder, read them back, line them up by time |
| `services_and_language_model.ipynb` | start and stop a service, handle a refusal, ask the language model, test a program that acts on its answer |
| `refusals_and_errors.ipynb` | what each error means, `set` and `move_to` when a pose is refused, the shape of a program that handles them |

**Moving the arms**, best read in this order, since each uses the one before:

| Module | What it shows |
|---|---|
| `joints_and_frames.ipynb` | read the joints, forward kinematics from the robot's description file, how far the arm lags the command |
| `trajectories.ipynb` | a step, a minimum-jerk move streamed by hand, and faster moves until the 2 rad/s limit takes over |
| `inverse_kinematics.ipynb` | a numerical Jacobian and damped-least-squares IK; send the answers and handle a refused pose |
| `perception.ipynb` | find the red ball in the head camera, turn pixels into a 3-D point, point the right arm at it, closed loop |

## Run one

Install `g1lab` as the [README](../README.md) says, with `camera,mock`, then:

```
pip install jupyter matplotlib
jupyter notebook camera_and_depth.ipynb
```

Each notebook starts on the mock, the robot on your laptop. To run one in the lab,
set `HOST = "192.168.123.222"` and your name in `NAME`, in its first code cell. A module
that moves the arms needs a session the operator has started, or one from
`r.services.start("sim")`. The ones that only read sensors do not.

The Perception module on the real robot needs a real red ball, about 3 in across. The mock
has no depth, so Camera and depth uses made-up points there and says so.
