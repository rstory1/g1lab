#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Run mission_basic.yaml (find a cup, walk up to it, pick it up) on a laptop.

    pip install "g1lab[mock,missions]"     # missions: reads YAML files
    python3 mission_basic.py               # the YAML file
    python3 mission_basic.py --python      # the same mission, written in Python

The arms and their safety checks are the mock robot's own. The room, the walking and
the detector are pretend (g1lab.mockworld), so this tests your mission, not the robot.
"""

import os
import sys

import g1lab
from g1lab.mission import Mission
from g1lab.mockworld import MockWorld

r = g1lab.mock(name="example", settle=0.3)
# A cup 1.5 m ahead and 0.4 m to the left, 0.1 m above the pelvis (table height):
# x, y on the map (m), the robot starting at (0, 0) facing +x.
MockWorld(r, objects={"cup": (1.5, 0.4, 0.1)})

if "--python" in sys.argv:
    m = (Mission("fetch_cup", timeout=120)
         .find("cup", scan=True)
         .approach("cup", standoff=0.3)
         .pick("cup", hand="right", verify="none")     # the mock's touch pads read nothing
         .home(hands="keep"))
    result = m.run(r)
else:
    m = Mission.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mission_basic.yaml"))
    result = m.run(r, {"verify": "none"})               # params override, as --param does

print("status:", result.status)                         # done, failed, cancelled, timeout, error
if not result.ok:
    print("failed at step", result.failed_step, "-", result.message)
r.close()
sys.exit(0 if result.ok else 1)
