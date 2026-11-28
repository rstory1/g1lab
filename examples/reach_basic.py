#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Plan a right-hand reach to a point in front of the robot; with --move, do it.

    python3 reach_basic.py --move   # needs the arm simulator on: see the guide
    python3 reach_basic.py --x 0.9                  # too far: Unreachable
"""

import argparse

import g1lab
from g1lab.reach import ReachSolver, Unreachable

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--host", default="192.168.123.222", help="the robot computer")
ap.add_argument("--x", type=float, default=0.35, help="m forward of the pelvis")
ap.add_argument("--y", type=float, default=-0.15, help="m to the left (negative: right)")
ap.add_argument("--z", type=float, default=0.05, help="m up from the pelvis")
ap.add_argument("--move", action="store_true", help="move the arm there, not only plan")
a = ap.parse_args()

r = g1lab.connect(a.host)
solver = ReachSolver.from_info(r.info())            # uses this robot's own joint limits
try:
    plan = solver.plan("right", (a.x, a.y, a.z))    # the hand's grasp center on the point
except Unreachable as exc:
    print("unreachable:", exc)                      # says why: too far, or which joints hit a stop
    raise SystemExit(1)
print("grasp from the", plan.approach_name)         # side, top, ...
print("pre-grasp:", plan.pre.round(2))              # 7 arm angles (rad), 10 cm back from the point
print("grasp:    ", plan.grasp.round(2))

if a.move:
    with r.control() as c:
        c.hands.open("right")
        c.arms.move_to(right=plan.pre, duration=2.0)    # first the pre-grasp, then in
        c.arms.move_to(right=plan.grasp, duration=1.5)
        js = r.state.joints()                           # correct from the real angles, the waist's too
        plan, miss = solver.refine(plan, js.arm("right"), [js["waist_yaw"], js["waist_roll"], js["waist_pitch"]])
        print(f"the hand was {miss * 100:.1f} cm off; corrected")
        c.arms.move_to(right=plan.grasp, duration=0.5)
        c.arms.move_to(right=plan.pre, duration=1.5)    # back out the way it came
r.close()                                               # letting go: the arms go home
