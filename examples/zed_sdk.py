#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 The University of Iowa, Department of Mechanical Engineering
# SPDX-License-Identifier: Apache-2.0

"""The ZED SDK yourself: open the robot's camera stream with pyzed, compute your
own depth, and (with --objects) run the SDK's object detection. Read only: it
never opens the camera itself and cannot move the robot. Does not use g1lab.

    python3 zed_sdk.py                                  # the robot's stream, 10 s
    python3 zed_sdk.py --objects --seconds 30
    python3 zed_sdk.py --svo episode.svo2 --objects     # a recording, no robot

Needs an NVIDIA graphics card and the ZED SDK 5.x with its Python package
(pyzed): see docs/zed_sdk_direct.md, "Get pyzed" (any account, laptop or
robot computer: a venv plus the SDK's get_python_api.py). Depth runs on YOUR card; on the robot computer it shares the card with the
robot's controller, so keep NEURAL_LIGHT while the robot runs, and stop at once
if the operator asks. --picture saves the left picture cut to g1lab's 640 x 480
with the objects drawn on it (needs OpenCV).
"""

import argparse
import math
import sys
import time

STREAM_HOST, STREAM_PORT = "192.168.123.164", 30000      # the robot's camera server
PIC_W, PIC_H = 640, 480                                   # g1lab's r.camera.read() picture


def to_picture(x, y, w=1280, h=720):
    """A pixel of the stream's full 16:9 frame -> the same spot in g1lab's 640 x 480
    picture, which is the frame's 4:3 middle shrunk: drop the sides, then scale."""
    cut = w - h * PIC_W // PIC_H                    # 1280 - 960 = 320 pixels, half each side
    s = PIC_H / h                                   # 480 / 720 = 2/3
    return (x - cut / 2) * s, y * s


def open_camera(sl, a):
    init = sl.InitParameters()
    if a.svo:
        init.set_from_svo_file(a.svo)
        init.svo_real_time_mode = True              # play at the recorded speed
    else:
        init.set_from_stream(a.host, a.port)        # the robot's stream, never the camera itself
    init.depth_mode = getattr(sl.DEPTH_MODE, a.depth_mode)
    init.coordinate_units = sl.UNIT.METER
    init.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP_X_FWD   # x forward, y left, z up, as g1lab
    cam = sl.Camera()
    err = cam.open(init)
    if err != sl.ERROR_CODE.SUCCESS:
        sys.exit(f"cannot open {a.svo or f'{a.host}:{a.port}'} ({err}): is the robot on, "
                 f"and are you on the Robot Network?")
    if a.objects:
        # Object detection needs positional tracking. The stream sends the IMU too slowly
        # for the SDK's IMU fusion, so track from the pictures alone.
        pt = sl.PositionalTrackingParameters()
        pt.enable_imu_fusion = False
        if cam.enable_positional_tracking(pt) != sl.ERROR_CODE.SUCCESS:
            sys.exit("positional tracking did not start")
        od = sl.ObjectDetectionParameters()
        od.detection_model = sl.OBJECT_DETECTION_MODEL.MULTI_CLASS_BOX_MEDIUM
        od.enable_tracking = True
        print("starting object detection (the first time on a computer it prepares the model: minutes)")
        if cam.enable_object_detection(od) != sl.ERROR_CODE.SUCCESS:
            sys.exit("object detection did not start")
    return cam


def save_picture(path, image, objects, w, h):
    try:
        import cv2                                  # the ZED's own samples draw with OpenCV too
    except ImportError:
        sys.exit("--picture needs OpenCV: pip install opencv-python")
    bgra = image.get_data()                         # h x w x 4, blue-green-red-alpha
    cut = (w - h * PIC_W // PIC_H) // 2
    pic = cv2.resize(bgra[:, cut:w - cut, :3], (PIC_W, PIC_H), interpolation=cv2.INTER_AREA)
    for o in objects:
        corners = [to_picture(float(p[0]), float(p[1]), w, h) for p in o.bounding_box_2d]
        if corners:
            u0, v0 = int(min(c[0] for c in corners)), int(min(c[1] for c in corners))
            u1, v1 = int(max(c[0] for c in corners)), int(max(c[1] for c in corners))
            cv2.rectangle(pic, (u0, v0), (u1, v1), (0, 255, 0), 2)
            cv2.putText(pic, str(o.label).split(".")[-1], (u0 + 3, v0 + 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 1)
    cv2.imwrite(path, pic)
    print("saved", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=STREAM_HOST, help="the camera server's computer (default %(default)s)")
    ap.add_argument("--port", type=int, default=STREAM_PORT)
    ap.add_argument("--svo", help="play this SVO2 recording instead of the robot's stream")
    ap.add_argument("--depth-mode", default="NEURAL_LIGHT", choices=["NEURAL_LIGHT", "NEURAL", "NEURAL_PLUS"],
                    help="NEURAL_LIGHT (the default) is lightest on a shared graphics card")
    ap.add_argument("--objects", action="store_true", help="also run the SDK's object detection")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--picture", help="at the end, save the picture with the objects drawn (needs OpenCV)")
    a = ap.parse_args()
    try:
        import pyzed.sl as sl
    except ImportError as exc:
        sys.exit(f"cannot import pyzed ({exc}): install the ZED SDK, then run its get_python_api.py "
                 f"with this Python (zed_sdk_direct.md, \"Get pyzed\")")

    cam = open_camera(sl, a)
    try:
        info = cam.get_camera_information()
        cc = info.camera_configuration
        w, h = cc.resolution.width, cc.resolution.height
        left = cc.calibration_parameters.left_cam
        print(f"{info.camera_model} S/N {info.serial_number}, {w} x {h} at {cc.fps:.0f} fps, "
              f"fx {left.fx:.1f} (the 640 x 480 picture's: {left.fx * PIC_H / h:.1f}), SDK {sl.Camera.get_sdk_version()}")
        image, depth, objects = sl.Mat(), sl.Mat(), sl.Objects()
        rt = sl.RuntimeParameters()
        found = []
        end, next_print = time.time() + a.seconds, 0.0
        while time.time() < end:
            if cam.grab(rt) != sl.ERROR_CODE.SUCCESS:
                continue
            if time.time() < next_print:
                continue
            next_print = time.time() + 1.0
            cam.retrieve_measure(depth, sl.MEASURE.DEPTH)        # h x w meters, NaN / inf = none
            err, z = depth.get_value(w // 2, h // 2)
            print(f"straight ahead: {z:.2f} m" if math.isfinite(z) else "straight ahead: no depth")
            if a.objects:
                cam.retrieve_objects(objects, sl.ObjectDetectionRuntimeParameters())
                found = list(objects.object_list)
                for o in found:
                    u, v = to_picture(*o.bounding_box_2d[0], w, h) if len(o.bounding_box_2d) else (math.nan, math.nan)
                    x, y, zz = o.position
                    print(f"  {str(o.label).split('.')[-1]:<12} {o.confidence:3.0f} %  at x {x:5.2f}  y {y:5.2f}"
                          f"  z {zz:5.2f} m  box corner in the picture ({u:.0f}, {v:.0f})")
        if a.picture:
            cam.retrieve_image(image, sl.VIEW.LEFT)
            save_picture(a.picture, image, found, w, h)
    finally:
        cam.close()                                 # frees the graphics card at once


if __name__ == "__main__":
    main()
