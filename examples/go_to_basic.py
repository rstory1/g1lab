#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Walk to a point 1 m straight ahead with r.nav.go_to() and print how it ended.

    python3 go_to_basic.py --host mock --name YOURNAME             # laptop: the walking mock
    python3 go_to_basic.py --host 192.168.123.222 --name YOURNAME  # lab: the walking simulator
"""

import argparse
import math

import g1lab

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--host", default="mock", help="the robot computer, or mock")
ap.add_argument("--name", default="example")
ap.add_argument("--meters", type=float, default=1.0, help="how far ahead to go")
a = ap.parse_args()

if a.host == "mock":
    r = g1lab.mock(name=a.name, nav="lab")          # a pretend room, with the robot's safety rules
else:
    r = g1lab.connect(a.host, name=a.name)
    r.services.start("walk", wait=300)              # the walking simulator: about a minute to start

p = r.nav.pose()                                    # where the robot is: x, y (m) and yaw (rad) on the map
goal_x = p.x + a.meters * math.cos(p.yaw)           # a point straight ahead
goal_y = p.y + a.meters * math.sin(p.yaw)
print(f"from ({p.x:.2f}, {p.y:.2f}) to ({goal_x:.2f}, {goal_y:.2f})")

with r.control() as c:                              # waits for your turn
    h = r.nav.go_to(goal_x, goal_y, yaw=p.yaw, timeout=60)   # blocks until it ends
print("result:", h.result)                          # "arrived", "blocked", "no_path", "stopped", ...
if h.result != "arrived":
    print("why:", h.reason)                         # the reason, in words
print(f"ended at ({h.pose[0]:.2f}, {h.pose[1]:.2f}), {h.remaining_m:.2f} m from the goal")
r.close()
