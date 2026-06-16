extends Node3D

var udp := PacketPeerUDP.new()

@onready var viewport_cam: Camera3D = $"CameraViewport/ViewportCam"
@onready var cam_mount: Node3D = $"CameraMount"
@onready var drone_cam: Camera3D = $"CameraMount/DroneCamera"

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

	# ViewportCam lives inside SubViewport which has own_world_3d=false, so global_transform
	# is in the shared world space — copy DroneCamera's world pose directly.
	if viewport_cam and drone_cam:
		viewport_cam.global_position = drone_cam.global_position
		viewport_cam.global_rotation = drone_cam.global_rotation
