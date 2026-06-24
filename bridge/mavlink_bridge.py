"""MAVLink → UDP pose bridge for Godot.

Reads GLOBAL_POSITION_INT + ATTITUDE from PX4 SITL and sends local ENU pose
as JSON over UDP to localhost:5005 at ~30 Hz.

Usage:
    python3 bridge/mavlink_bridge.py [--mavlink-url URL] [--godot-port PORT]
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import time

from pymavlink import mavutil


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mavlink-url", default="udpin:0.0.0.0:14540")
    p.add_argument("--godot-port", type=int, default=5005)
    return p.parse_args()


def connect(url: str):
    print(f"[bridge] connecting to {url} ...")
    master = mavutil.mavlink_connection(url)
    # Send heartbeats first so PX4 learns our address and starts sending back.
    print("[bridge] priming PX4 with heartbeats, waiting for response ...")
    deadline = time.time() + 30
    while time.time() < deadline:
        master.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0, 0, 0,
        )
        msg = master.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        if msg:
            print(f"[bridge] heartbeat OK (sys={master.target_system})")
            return master
    raise RuntimeError("No heartbeat from PX4 after 30s")


def send_heartbeat(master, last: list[float]) -> None:
    now = time.time()
    if now - last[0] >= 1.0:
        master.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0, 0, 0,
        )
        last[0] = now


def main() -> None:
    args = parse_args()
    master = connect(args.mavlink_url)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    home_lat = home_lon = None
    lat = lon = rel_alt = 0.0
    roll = pitch = yaw = 0.0
    have_pos = False

    last_hb = [0.0]
    last_send = time.time()
    interval = 1.0 / 30.0

    print(f"[bridge] streaming to localhost:{args.godot_port} at 30 Hz")

    while True:
        send_heartbeat(master, last_hb)

        # drain all pending messages
        while True:
            msg = master.recv_match(
                type=["GLOBAL_POSITION_INT", "ATTITUDE"],
                blocking=False,
            )
            if msg is None:
                break
            t = msg.get_type()
            if t == "GLOBAL_POSITION_INT":
                lat = msg.lat / 1e7
                lon = msg.lon / 1e7
                rel_alt = msg.relative_alt / 1000.0
                if home_lat is None:
                    home_lat, home_lon = lat, lon
                    print(f"[bridge] home set: {home_lat:.6f}, {home_lon:.6f}")
                have_pos = True
            elif t == "ATTITUDE":
                roll = msg.roll    # radians
                pitch = msg.pitch
                yaw = msg.yaw

        now = time.time()
        if have_pos and (now - last_send) >= interval:
            # equirectangular ENU (meters from home)
            cos_lat = math.cos(math.radians(home_lat))
            x = (lon - home_lon) * cos_lat * 111320.0   # East
            y = (lat - home_lat) * 111320.0              # North
            z = rel_alt                                  # Up

            payload = json.dumps({
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(z, 3),
                "roll": round(roll, 4),
                "pitch": round(pitch, 4),
                "yaw": round(yaw, 4),
            }).encode()
            sock.sendto(payload, ("127.0.0.1", args.godot_port))
            last_send = now
        else:
            time.sleep(0.001)


if __name__ == "__main__":
    main()
