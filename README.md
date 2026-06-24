# PX4 + Gazebo → Godot 4 → QGroundControl

Live drone telemetry and camera stream: PX4 SITL physics → Godot 3D world → QGroundControl video.

## Architecture

```
PX4 SITL (Gazebo Harmonic)
  │  MAVLink UDP :14540        ← also exposed on :14550 for QGC
  ▼
bridge/mavlink_bridge.py
  │  JSON UDP :5005 @ 30 Hz   {x,y,z,roll,pitch,yaw}
  ▼
Godot 4  (new-game-project/)
  │  drone_controller.gd moves Drone node
  │  SubViewport renders drone-camera FOV
  │  CanvasLayer TextureRect shows viewport fullscreen
  ▼
bridge/godot_capture.py
  │  mss screen-captures Godot window
  │  ffmpeg pipe → H.264 RTSP
  ▼
mediamtx RTSP server :8554
  ▼
QGroundControl  (RTSP video source)
```

## Prerequisites

| Tool | Version |
|------|---------|
| PX4-Autopilot | cloned to `~/PX4-Autopilot` (or set `$PX4_DIR`) |
| Gazebo Harmonic | `gz-harmonic` |
| Godot 4 | 4.x on PATH as `godot` (or set `$GODOT_BIN`) |
| mediamtx | installed by `setup.sh` or set `$MEDIAMTX_BIN` |
| Python 3.9+ | with pip |
| ffmpeg | `apt install ffmpeg` |
| wmctrl | `apt install wmctrl` (for window detection) |

## Install

```bash
./setup.sh          # installs mediamtx + Python deps
```

Or manually:

```bash
pip install -r bridge/requirements.txt
```

## Run

```bash
./launch.sh
```

This starts (in order):

1. **mediamtx** — RTSP server on `:8554`
2. **PX4 SITL + Gazebo** — `make px4_sitl gz_x500` in `$PX4_DIR`
3. **mavlink_bridge.py** — reads telemetry, sends ENU pose to Godot
4. **Godot** — renders 3D world with drone; drone-camera view shown fullscreen
5. **godot_capture.py** — captures Godot window → ffmpeg → RTSP

## QGroundControl setup

1. Open QGroundControl
2. **Application Settings → General → Video** (or Comm Links for MAVLink)
3. MAVLink: auto-connects on UDP `14550` (PX4 SITL default output)
4. Video source: **RTSP Video Stream** → `rtsp://localhost:8554/drone`

## Per-component config

```bash
# Custom MAVLink port or Godot UDP port:
python3 bridge/mavlink_bridge.py --mavlink-url udpin:0.0.0.0:14540 --godot-port 5005

# Custom RTSP target:
python3 bridge/godot_capture.py --rtsp-url rtsp://localhost:8554/drone --width 1280 --height 720

# Custom PX4 dir or Godot binary:
PX4_DIR=~/my-px4 GODOT_BIN=/opt/godot ./launch.sh
```

## File layout

```
px4-godot/
├── bridge/
│   ├── mavlink_bridge.py   # MAVLink → UDP JSON pose
│   ├── godot_capture.py    # screen capture → ffmpeg RTSP
│   └── requirements.txt
├── new-game-project/
│   ├── scenes/
│   │   └── drone_world.tscn   # 3D world + drone + camera viewport
│   ├── scripts/
│   │   ├── drone_controller.gd  # UDP pose receiver → Node3D transform
│   │   └── camera_streamer.gd   # wires SubViewport → TextureRect
│   └── project.godot
├── launch.sh
├── setup.sh
└── README.md
```
