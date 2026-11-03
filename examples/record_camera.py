#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""Record the head camera to a folder of JPEGs, for labelling or training.
Needs no session; the robot does not move.

    python3 record_camera.py --host 192.168.123.222 --name YOURNAME --seconds 30
    python3 record_camera.py --host 192.168.123.222 --name YOURNAME --fps 2 --out mugs
    python3 record_camera.py --host 192.168.123.222 --name YOURNAME --video  # also an MP4

Writes <out>/frame_00001.jpg ... and <out>/frames.csv (frame, camera time,
time saved). Pictures are 640 x 480, the left eye, at most 15 a second.
--video needs OpenCV (`pip install opencv-python`, or g1lab's `video` option).
"""

import argparse
import csv
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
    ap.add_argument("--out", default=time.strftime("camera_%Y%m%d_%H%M%S"))
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--fps", type=float, default=15.0, help="pictures a second to keep (15 is all)")
    ap.add_argument("--video", action="store_true", help="also write <out>/video.mp4 (needs OpenCV)")
    a = ap.parse_args()
    if a.video:
        try:
            import cv2  # noqa: F401
        except ImportError:
            sys.exit("--video needs OpenCV: pip install opencv-python (the pictures alone do not)")

    r = (g1lab.mock(name=a.name) if a.host == "mock"
         else g1lab.connect(a.host, name=a.name, port=a.port))
    os.makedirs(a.out, exist_ok=True)
    video = None
    n, last_t, next_keep = 0, None, 0.0
    end = time.time() + a.seconds
    with open(os.path.join(a.out, "frames.csv"), "w", newline="") as fh:
        log = csv.writer(fh)
        log.writerow(["frame", "camera_time", "saved_time"])
        while time.time() < end:
            t, jpeg = r.camera.jpeg()
            if t == last_t or time.time() < next_keep:   # same picture, or too soon
                time.sleep(0.005)
                continue
            last_t, next_keep = t, time.time() + 1.0 / a.fps
            n += 1
            name = os.path.join(a.out, f"frame_{n:05d}.jpg")
            with open(name, "wb") as img:
                img.write(jpeg)
            log.writerow([n, f"{t:.3f}", f"{time.time():.3f}"])
            if a.video:
                import cv2
                import numpy as np
                frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                if video is None:
                    h, w = frame.shape[:2]
                    video = cv2.VideoWriter(os.path.join(a.out, "video.mp4"),
                                            cv2.VideoWriter_fourcc(*"mp4v"), min(a.fps, 15.0), (w, h))
                video.write(frame)
            print(f"\r{n} pictures", end="", flush=True)
    if video is not None:
        video.release()
    r.close()
    print(f"\nsaved {n} pictures in {a.out}/")


if __name__ == "__main__":
    try:
        main()
    except g1lab.G1LabError as exc:
        sys.exit(f"{type(exc).__name__}: {exc}")
    except KeyboardInterrupt:
        print("\nstopped")
