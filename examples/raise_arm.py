#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Raise the right arm forward, hold it, then let go.

The arm stays up for 20 s (--seconds) while the program just sleeps: g1lab
keeps the pose held for you. When the program lets go, the arms go home.

    python3 raise_arm.py --host mock --name YOURNAME             # on your laptop
    python3 raise_arm.py --host 192.168.123.222 --name YOURNAME  # in the lab
"""

import argparse
import math
import os
import sys
import time

try:
    import g1lab
except ImportError:                     # run from the repo, not installed
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    import g1lab


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="localhost", help="the robot computer, or mock")
    ap.add_argument("--port", type=int, default=5600)
    ap.add_argument("--name", default="example")
    ap.add_argument("--seconds", type=float, default=20.0, help="how long to hold the arm up")
    a = ap.parse_args()

    r = (g1lab.mock(name=a.name) if a.host == "mock"     # a laptop, no robot
         else g1lab.connect(a.host, name=a.name, port=a.port))
    arm = r.info().home["right_arm"].copy()
    arm[0] = math.radians(-60)              # shoulder_pitch: raise the arm forward
    arm[3] = math.radians(20)               # elbow
    with r.control() as c:
        try:
            c.arms.move_to(right=arm, duration=2.0)
        except g1lab.Refused as exc:        # e.g. a hand would hit the body
            print("refused:", exc.reason)
            return
        print("arm up; holding")
        time.sleep(a.seconds)               # the robot keeps the pose: g1lab keeps sending
        print("status:", c.status)
    print("done: the arm goes home")        # leaving the block lets go of the robot
    r.close()


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
