extends Node3D

var udp := PacketPeerUDP.new()

func _ready() -> void:
	udp.bind(5005)

func _process(_delta: float) -> void:
	while udp.get_available_packet_count() > 0:
		var pkt := udp.get_packet()
		var txt := pkt.get_string_from_utf8()
		var data = JSON.parse_string(txt)
		if data == null:
			continue
		# ENU → Godot: East=x, Up=y, South=z (right-hand → left-hand)
		position = Vector3(data["x"], data["z"], -data["y"])
		# roll→x, pitch→z (negated), yaw→y (negated) in Godot convention
		rotation = Vector3(data["roll"], -data["yaw"], -data["pitch"])
