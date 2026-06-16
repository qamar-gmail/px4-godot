extends Node3D

var udp := PacketPeerUDP.new()

@onready var drone_cam: Camera3D = $"CameraMount/DroneCamera"
# Main scene camera that actually renders — follows drone_cam every frame
@onready var main_cam: Camera3D = $"/root/DroneWorld/MainCamera"

func _ready() -> void:
	udp.bind(5005)

func _process(_delta: float) -> void:
	while udp.get_available_packet_count() > 0:
		var pkt := udp.get_packet()
		var txt := pkt.get_string_from_utf8()
		var data = JSON.parse_string(txt)
		if data == null:
			continue
		# ENU → Godot: East=x, Up=y, South=z
		position = Vector3(data["x"], data["z"], -data["y"])
		rotation = Vector3(data["roll"], -data["yaw"], -data["pitch"])

	# Drive the main scene camera to match the drone camera's world pose
	if main_cam and drone_cam:
		main_cam.global_transform = drone_cam.global_transform
