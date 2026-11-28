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

Install `g1lab` as the [README](../README.md) says, in your own account on the lab
workstation (you log in with your university ID), then:

```
pip install jupyter matplotlib mujoco        # mujoco is for Joints and frames only
cd notebooks
jupyter notebook camera_and_depth.ipynb
```

Start Jupyter in this folder: Joints and frames, Inverse kinematics and Perception read
`g1_29dof_dx3_ros.urdf`, the robot's description file, from the folder they are in.

Each notebook connects to the lab workstation at `192.168.123.222`. A module that moves the
arms needs the robot on: turn the arm simulator on with `r.services.start("sim")`.
`print(r.info().features)` says what is on.
The ones that only read sensors do not.

For now the modules that move the arms run on the lab simulator; the same program runs on
the real robot unchanged once the arms open there. The modules that only read sensors run
on the real robot today. Camera and depth needs a real red ball, about 3 in across, there:
the lab simulator has no depth, so it uses made-up points there and says so.
