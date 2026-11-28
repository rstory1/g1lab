#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Walk to a point 1 m straight ahead with r.nav.go_to() and print how it ended.
"arrived" means within the tolerance of the goal, in a straight line: 0.15 m unless you pass tolerance=.

    python3 go_to_basic.py      # the lab simulator, walking
"""

import argparse
import math

import g1lab

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--host", default="192.168.123.222", help="the robot computer")
ap.add_argument("--meters", type=float, default=1.0, help="how far ahead to go")
a = ap.parse_args()

r = g1lab.connect(a.host)
r.services.start("walk", wait=300)                  # the walking simulator: about a minute to start

p = r.nav.pose()                                    # where the robot is: x, y (m) and yaw (rad) on the map
goal_x = p.x + a.meters * math.cos(p.yaw)           # a point straight ahead
goal_y = p.y + a.meters * math.sin(p.yaw)
print(f"from ({p.x:.2f}, {p.y:.2f}) to ({goal_x:.2f}, {goal_y:.2f})")

with r.control() as c:                              # waits until the robot is free
    h = r.nav.go_to(goal_x, goal_y, yaw=p.yaw, timeout=60)   # blocks until it ends
print("result:", h.result)                          # "arrived", "blocked", "no_path", "stopped", ...
if h.result != "arrived":
    print("why:", h.reason)                         # the reason, in words
straight = math.hypot(goal_x - h.pose[0], goal_y - h.pose[1])
print(f"ended at ({h.pose[0]:.2f}, {h.pose[1]:.2f}), {straight:.2f} m from the goal in a straight "
      f"line (arrived counts within 0.15 m; h.remaining_m measures along the planned path, "
      f"so it can read more)")
r.close()
