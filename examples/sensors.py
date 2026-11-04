#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Read the robot without moving it: joints, body tilt, the right hand, the
temperatures and one camera picture. Needs no session.

    python3 sensors.py --host 192.168.123.222 --picture view.jpg
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
    ap.add_argument("--picture", help="save one camera picture (JPEG) here")
    a = ap.parse_args()

    r = (g1lab.mock(name=a.name) if a.host == "mock"     # a laptop, no robot
         else g1lab.connect(a.host, name=a.name, port=a.port))
    try:
        js = r.state.joints()
        print("right arm (deg):", [round(math.degrees(v), 1) for v in js.arm("right")])
        print("right elbow (deg):", round(math.degrees(js["R_elbow"]), 1))
        roll, pitch, yaw = r.state.imu().rpy
        print(f"body tilt: roll {math.degrees(roll):.1f}, pitch {math.degrees(pitch):.1f} deg")
        hand = r.hands.state("right")
        print("right hand pads:", dict(zip(hand.pad_names, hand.pads.round(2).tolist())))
        hot = r.state.temps().get("hottest")
        if hot:
            print(f"hottest motor: {hot['where']} at {hot['c']:.0f} C")
    except g1lab.NoData as exc:
        print("no reading:", exc)

    count = {"n": 0}
    stop = r.on("joints", lambda js: count.update(n=count["n"] + 1))
    time.sleep(2.0)
    stop()
    print(f"joints arrive {count['n'] / 2.0:.0f} times a second")

    if a.picture:
        try:
            t, jpeg = r.camera.jpeg()
            with open(a.picture, "wb") as fh:
                fh.write(jpeg)
            print("saved", a.picture)
        except g1lab.NoData as exc:
            print("no picture:", exc)
    r.close()


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
