"""Receive raw RGBA frames from Godot's SubViewport over TCP and pipe to ffmpeg.

Godot runs scripts/viewport_streamer.gd which pushes frames on TCP port 5006.
This script connects, reads width/height header + RGBA data, converts to BGR,
and feeds ffmpeg → mediamtx RTSP + QGC UDP RTP on port 5600.

Usage:
    python3 bridge/godot_capture.py [--godot-host H] [--godot-port P]
                                     [--rtsp-url URL] [--udp-port PORT]
"""

from __future__ import annotations

import argparse
import socket
import struct
import subprocess
import sys
import time

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--godot-host", default="127.0.0.1")
    p.add_argument("--godot-port", type=int, default=5006)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--rtsp-url", default="rtsp://localhost:8554/drone")
    p.add_argument("--udp-port", type=int, default=5600)
    return p.parse_args()


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Godot disconnected")
        buf += chunk
    return buf


def connect_to_godot(host: str, port: int, timeout: float = 60.0) -> socket.socket:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.settimeout(None)
            print(f"[capture] connected to Godot on {host}:{port}")
            return s
        except OSError:
            print(f"[capture] waiting for Godot on {host}:{port} ...")
            time.sleep(2)
    raise RuntimeError(f"Could not connect to Godot after {timeout}s")


def make_ffmpeg(W: int, H: int, rtsp_url: str, udp_port: int) -> subprocess.Popen:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-f", "rawvideo", "-pixel_format", "bgr24",
        "-video_size", f"{W}x{H}", "-framerate", "30",
        "-i", "pipe:0",
        # output 1: RTSP → mediamtx
        "-c:v", "libx264", "-preset", "ultrafast",
        "-tune", "zerolatency", "-pix_fmt", "yuv420p",
        "-f", "rtsp", "-rtsp_transport", "udp", rtsp_url,
        # output 2: RTP/UDP → QGC port 5600
        "-c:v", "libx264", "-preset", "ultrafast",
        "-tune", "zerolatency", "-pix_fmt", "yuv420p",
        "-f", "rtp", f"rtp://127.0.0.1:{udp_port}",
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def main() -> None:
    args = parse_args()
    W, H = args.width, args.height

    print(f"[capture] will stream to {args.rtsp_url} and UDP {args.udp_port}")

    while True:
        try:
            godot = connect_to_godot(args.godot_host, args.godot_port)
        except RuntimeError as e:
            print(f"[capture] {e}, retrying...")
            time.sleep(5)
            continue

        ffmpeg = make_ffmpeg(W, H, args.rtsp_url, args.udp_port)

        try:
            while True:
                # read header: width (4B LE) + height (4B LE)
                hdr = recv_exact(godot, 8)
                w, h = struct.unpack_from("<II", hdr)
                raw = recv_exact(godot, w * h * 4)  # RGBA

                # RGBA → BGR, resize if needed
                frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 4))
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                if w != W or h != H:
                    bgr = cv2.resize(bgr, (W, H))

                ffmpeg.stdin.write(bgr.tobytes())

        except (ConnectionError, BrokenPipeError) as e:
            print(f"[capture] connection lost: {e}, reconnecting...")
            ffmpeg.stdin.close()
            ffmpeg.wait()


if __name__ == "__main__":
    main()
