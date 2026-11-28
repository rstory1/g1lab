#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Check you can reach the robot: print whether it is on, who has it, what features
are on, the joint names, the limits and the home pose. Works with the robot off.

    python3 info.py --host 192.168.123.222
"""

import argparse
import math
import os
import sys

try:
    import g1lab
except ImportError:                     # run from the repo, not installed
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    import g1lab


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="192.168.123.222", help="the robot computer")
    ap.add_argument("--port", type=int, default=5600)
    a = ap.parse_args()

    r = g1lab.connect(a.host, port=a.port)
    info = r.info()
    print(f"robot: {info.robot}   has the robot: {info.owner or 'nobody'}")
    print(info.features)       # what is on, and for each thing that is off, what turns it on
    for g, names in info.groups.items():
        print(f"\n{g}")
        for name, (lo, hi), h in zip(names, info.limits[g], info.home[g]):
            fixed = "   (fixed: this joint does not move)" if lo == hi else ""
            print(f"  {name:15s} {math.degrees(lo):7.1f} .. {math.degrees(hi):6.1f} deg"
                  f"   home {math.degrees(h):6.1f}{fixed}")
    r.close()


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
