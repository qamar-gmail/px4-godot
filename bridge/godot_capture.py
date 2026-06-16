"""Screen-capture the Godot window and pipe frames to ffmpeg → mediamtx RTSP.

Finds the Godot window by title ("px4-godot"), captures it at 30 fps,
and sends raw BGR frames to ffmpeg which outputs an RTSP stream.

Usage:
    python3 bridge/godot_capture.py [--width W] [--height H] [--rtsp-url URL]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

import mss
from mss import MSS as MSSClass
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--rtsp-url", default="rtsp://localhost:8554/drone")
    return p.parse_args()


def find_godot_window() -> dict | None:
    """Return mss monitor dict for the Godot window, or None if not found."""
    try:
        import subprocess as sp
        out = sp.check_output(["wmctrl", "-lG"], text=True)
        for line in out.splitlines():
            if "px4-godot" in line.lower():
                parts = line.split()
                # wmctrl -lG: id desktop x y w h machine title
                x, y, w, h = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
                return {"left": x, "top": y, "width": w, "height": h}
    except Exception:
        pass
    return None


def main() -> None:
    args = parse_args()
    W, H = args.width, args.height

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pixel_format", "bgr24",
        "-video_size", f"{W}x{H}",
        "-framerate", "30",
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-f", "rtsp",
        "-rtsp_transport", "udp",
        args.rtsp_url,
    ]

    import os
    if not os.environ.get("DISPLAY"):
        # try common fallback
        for d in (":0", ":1"):
            import subprocess as _sp
            if _sp.run(["xdpyinfo", "-display", d], capture_output=True).returncode == 0:
                os.environ["DISPLAY"] = d
                break
    if not os.environ.get("DISPLAY"):
        print("[capture] ERROR: no X display found — run inside a desktop session")
        sys.exit(1)

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    interval = 1.0 / 30.0

    print(f"[capture] streaming to {args.rtsp_url}")
    print("[capture] looking for 'px4-godot' window ...")

    with MSSClass() as sct:
        monitor = None
        while True:
            t0 = time.time()

            if monitor is None:
                monitor = find_godot_window()
                if monitor is None:
                    # ponytail: fall back to primary monitor until window appears
                    monitor = sct.monitors[1]
                    print("[capture] Godot window not found, capturing primary monitor")

            frame = np.array(sct.grab(monitor))[:, :, :3]  # drop alpha → BGR
            # resize if captured monitor doesn't match target resolution
            if frame.shape[1] != W or frame.shape[0] != H:
                import cv2
                frame = cv2.resize(frame, (W, H))

            try:
                proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                print("[capture] ffmpeg pipe closed, exiting")
                sys.exit(1)

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0:
                time.sleep(sleep)


if __name__ == "__main__":
    main()
