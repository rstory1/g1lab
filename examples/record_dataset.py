#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Record the sensors to a folder, then read them back on one clock.
Needs no session; the robot does not move.

    python3 record_dataset.py --host mock --seconds 5
    python3 record_dataset.py --host 192.168.123.222 --name YOURNAME --seconds 30 --out hallway

About 1.5 MB a second without depth, so a minute is about 90 MB. Prints what
it got, then each lidar reading (or, on the mock, each odometry reading) next
to the joints at that moment.
"""

import argparse
import os
import sys

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
    ap.add_argument("--out", default=None, help="folder to write (default recording_<date>_<time>)")
    ap.add_argument("--seconds", type=float, default=10.0)
    a = ap.parse_args()

    r = (g1lab.mock(name=a.name, nav="lab") if a.host == "mock"
         else g1lab.connect(a.host, name=a.name, port=a.port))
    with r:
        rec = g1lab.Recorder(r, a.out).run(a.seconds)
    print(rec)

    topic = "lidar" if "lidar" in rec.topics else "odom"
    for k, (t, _) in enumerate(rec.read(topic, raw=True)):
        if k % 10 == 0:
            joints = rec.at("joints", t)
            if joints is not None:
                print(f"{t - rec.t0:6.2f} s  {topic}, joints {t - joints[0]:.3f} s before it: "
                      f"R elbow {joints[1]['R_elbow']:+.3f} rad")
    rec.close()


if __name__ == "__main__":
    main()
