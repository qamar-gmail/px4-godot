extends Node

# Wires the SubViewport texture to the fullscreen TextureRect at runtime.
# The actual streaming is handled externally by bridge/godot_capture.py.

@onready var viewport: SubViewport = $"/root/DroneWorld/Drone/CameraViewport"
@onready var display: TextureRect = $"/root/DroneWorld/CameraDisplay/TextureRect"

func _ready() -> void:
	if viewport and display:
		display.texture = viewport.get_texture()
