#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Hold the right arm out, as if carrying something, and walk a short way.

    python3 carry_while_walking.py      # the lab simulator, walking
"""

import argparse
import math

import g1lab

RIGHT_FORWARD = [-0.9, 0.1, 0.0, 0.9, 0.0, 0.0, 0.0]   # 7 angles (rad): forearm forward, elbow bent

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--host", default="192.168.123.222", help="the robot computer")
ap.add_argument("--meters", type=float, default=1.0)
a = ap.parse_args()

r = g1lab.connect(a.host)
r.services.start("walk", wait=300)                      # walking, and the arms are yours too
print("arms while walking:", r.info().arms)  # True: you may move them while walking

p = r.nav.pose()
with r.control() as c:
    c.arms.move_to(right=RIGHT_FORWARD, duration=3.0)  # raise the arm first, standing still
    c.hands.close("right", amount=0.5)                 # a loose grip
    h = r.nav.go_to(p.x + a.meters * math.cos(p.yaw), p.y + a.meters * math.sin(p.yaw), yaw=p.yaw)
    print("walk:", h.result, h.reason or "")           # the arm stayed where you put it
    print("arm now:", [round(float(v), 2) for v in r.state.joints().arm("right")])
    c.arms.home()                                      # put it down before letting go
r.close()
