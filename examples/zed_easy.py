#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""The ZED's depth image, objects, people and pose, the easy way: through g1lab,
with nothing else to install. Needs no session; the robot does not move.

    python3 zed_easy.py --host 192.168.123.222 --name YOURNAME
    python3 zed_easy.py --host 192.168.123.222 --name YOURNAME --seconds 30 --picture seen.jpg

Starts the zed service on the workstation (a few seconds), then once a second
prints what the ZED sees. --picture saves the camera picture with the boxes,
the skeletons and a few distances drawn on it (needs Pillow: g1lab's `camera`
option). The service stops by itself when nobody uses it.
The mock has no ZED: there it says so and stops.
"""

import argparse
import math
import os
import sys
import time

import numpy as np

try:
    import g1lab
except ImportError:                     # run from the repo, not installed
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    import g1lab

BONES = [("nose", "neck"), ("neck", "r_shoulder"), ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
         ("neck", "l_shoulder"), ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"), ("neck", "r_hip"),
         ("r_hip", "r_knee"), ("r_knee", "r_ankle"), ("neck", "l_hip"), ("l_hip", "l_knee"),
         ("l_knee", "l_ankle")]                      # BODY_18, the part worth drawing


def centre_depth(depth):
    """The distance (m) straight ahead: the median of a 20 x 20 patch in the middle."""
    h, w = depth.shape
    patch = depth[h // 2 - 10:h // 2 + 10, w // 2 - 10:w // 2 + 10]
    return float(np.nanmedian(patch)) if np.isfinite(patch).any() else math.nan


def report(r):
    """One line about each thing the ZED sees right now."""
    t, depth = r.depth.image()                      # 480 x 640 metres, NaN = not measured
    print(f"depth: {centre_depth(depth):.2f} m straight ahead, "
          f"{100 * np.isfinite(depth).mean():.0f} % of pixels measured")
    for o in r.zed.objects():
        print(f"  {o.label:<12} {o.confidence:3.0f} %  at x {o.position[0]:5.2f}  y {o.position[1]:5.2f}"
              f"  z {o.position[2]:5.2f} m  box {o.bbox and [round(v) for v in o.bbox]}")
    for b in r.zed.bodies():
        w = b.kp("r_wrist")
        where = f"{w.round(2).tolist()} m" if np.isfinite(w).all() else "not seen"
        print(f"  person {b.id}: right wrist {where}")
    p = r.zed.pose()
    print(f"  camera at {p.position.round(3).tolist()} m, tracking {p.tracking_state}")


def save_picture(r, path):
    """The camera picture with what the ZED found drawn on it. Depth, boxes and keypoints
    are all in the picture's own pixels, so nothing needs converting."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("--picture needs Pillow: pip install pillow (or g1lab's camera option)")
    import io
    _, jpeg = r.camera.jpeg()
    _, depth = r.depth.image()
    img = Image.open(io.BytesIO(jpeg)).convert("RGB")
    d = ImageDraw.Draw(img)
    for o in r.zed.objects():
        if o.bbox is not None:
            d.rectangle(o.bbox, outline=(0, 255, 0), width=2)
            d.text((o.bbox[0] + 3, o.bbox[1] + 3), f"{o.label} {o.position[0]:.1f} m", fill=(0, 255, 0))
    for b in r.zed.bodies():
        for a, c in BONES:
            pa = b.keypoints_2d[b.names.index(a)]
            pc = b.keypoints_2d[b.names.index(c)]
            if np.isfinite(pa).all() and np.isfinite(pc).all():
                d.line([tuple(pa), tuple(pc)], fill=(255, 0, 255), width=3)
    for u, v in ((160, 240), (320, 240), (480, 240), (320, 400)):    # a few distances
        z = depth[v, u]
        d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 255, 0))
        d.text((u + 5, v - 6), "?" if not np.isfinite(z) else f"{z:.2f} m", fill=(255, 255, 0))
    img.save(path)
    print("saved", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="localhost", help="the robot computer, or mock")
    ap.add_argument("--port", type=int, default=5600)
    ap.add_argument("--name", default="example")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--picture", help="save the picture with what the ZED found drawn on it (JPEG or PNG)")
    a = ap.parse_args()

    r = (g1lab.mock(name=a.name) if a.host == "mock"
         else g1lab.connect(a.host, name=a.name, port=a.port))
    try:
        print("starting the zed service ...")
        r.services.start("zed", wait=180)            # minutes only the very first time on a computer
        if a.host != "mock":                         # (the mock never has any: no point waiting)
            r.depth.image(timeout=60)                # "running" comes a few seconds before the first data
        end = time.time() + a.seconds
        while True:
            report(r)
            if time.time() >= end:
                break
            time.sleep(1.0)
        if a.picture:
            save_picture(r, a.picture)
    except g1lab.NoData as exc:
        print("no ZED data:", exc)
    finally:
        r.services.stop("zed")                       # others using it keep it running
        r.close()


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
