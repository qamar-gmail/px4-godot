#!/bin/bash
# PX4 + Gazebo + Godot + QGC video streaming launcher
set -e

PX4_DIR=${PX4_DIR:-"$HOME/dev/PX4-Autopilot"}
GODOT_BIN=${GODOT_BIN:-"godot"}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GODOT_PROJECT="$SCRIPT_DIR/new-game-project"
MEDIAMTX_BIN=${MEDIAMTX_BIN:-"mediamtx"}

# add ~/.local/bin to PATH in case mediamtx was installed there by setup.sh
export PATH="$HOME/.local/bin:$PATH"

# source ROS/Gazebo environment if not already set
if [ -z "$GZ_CONFIG_PATH" ] && [ -f /opt/ros/jazzy/setup.bash ]; then
  source /opt/ros/jazzy/setup.bash
fi

cleanup() {
  echo "[launch] shutting down..."
  kill 0
}
trap cleanup EXIT

# 1. mediamtx RTSP server
echo "[1/5] Starting mediamtx RTSP server..."
"$MEDIAMTX_BIN" "$SCRIPT_DIR/mediamtx.yml" &
sleep 2

# 2. PX4 SITL + Gazebo
echo "[2/5] Starting PX4 SITL with Gazebo..."
(cd "$PX4_DIR" && make px4_sitl gz_x500) &
echo "[launch] Waiting 30s for PX4+Gazebo to boot..."
sleep 30

# 3. MAVLink bridge
echo "[3/5] Starting MAVLink bridge..."
python3 "$(dirname "$0")/bridge/mavlink_bridge.py" &
sleep 3

# 4. Godot world
echo "[4/5] Starting Godot world..."
"$GODOT_BIN" --path "$GODOT_PROJECT" --scene scenes/drone_world.tscn -- &
sleep 5

# 5. Camera capture + RTSP stream
echo "[5/5] Starting camera stream..."
python3 "$(dirname "$0")/bridge/godot_capture.py" &

echo ""
echo "====================================="
echo "System ready!"
echo "QGroundControl: connect to UDP 14550"
echo "Video feed:     rtsp://localhost:8554/drone"
echo "====================================="
wait
