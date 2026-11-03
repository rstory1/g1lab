#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Wave the right arm and open and close the right hand: student_client.py
with g1lab. Copy it and change `pose_at`.

    python3 wave.py --host 192.168.123.222 --name ana
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


def pose_at(t, home):
    """The joint angles (rad) at `t` seconds. Start from home, change a few."""
    right_arm = home["right_arm"].copy()
    right_arm[0] = -1.2                                     # shoulder_pitch: arm forward and up
    right_arm[3] = 0.3                                      # elbow
    right_arm[2] = 0.4 * math.sin(2 * math.pi * 0.3 * t)    # shoulder_yaw: a slow wave
    close = 0.5 - 0.5 * math.cos(2 * math.pi * 0.2 * t)     # 0 open .. 1 closed
    return right_arm, close


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="localhost", help="the robot computer, or mock")
    ap.add_argument("--port", type=int, default=5600)
    ap.add_argument("--name", default="example")
    ap.add_argument("--seconds", type=float, default=30.0)
    a = ap.parse_args()

    r = (g1lab.mock(name=a.name) if a.host == "mock"     # a laptop, no robot
         else g1lab.connect(a.host, name=a.name, port=a.port))
    home = r.info().home
    with r.control() as c:                  # waits for your turn; the arms ease into home first
        print("the robot is following you")
        right_arm, _ = pose_at(0.0, home)
        c.arms.move_to(right=right_arm, duration=2.0)       # no jump to the first pose
        t0 = time.time()
        last = None
        while time.time() - t0 < a.seconds:
            right_arm, close = pose_at(time.time() - t0, home)
            c.arms.set(right=right_arm)
            c.hands.close("right", close)
            # Say each new answer once: clamps, held, resting, refusals.
            s = c.status
            note = (s.refused, s.held, sorted(s.resting), str(s.clamped))
            if note != last:
                last = note
                print(f"phase {s.phase}  clamped {s.clamped}  held {s.held}  "
                      f"resting {s.resting}  refused {s.refused}")
            time.sleep(1 / 30)              # the keepalive sends; this is only how often we change it
    print("done: the arms go home")
    r.close()


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
