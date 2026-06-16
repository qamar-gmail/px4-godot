extends Node3D

var udp := PacketPeerUDP.new()

# ViewportCam mirrors DroneCamera so the SubViewport shows the drone's POV
@onready var viewport_cam: Camera3D = $"CameraViewport/ViewportCam"
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

	# sync viewport camera to match drone's world transform
	if viewport_cam and drone_cam:
		viewport_cam.global_transform = drone_cam.global_transform
