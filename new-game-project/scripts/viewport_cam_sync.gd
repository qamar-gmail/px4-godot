extends Camera3D

# Runs inside SubViewport — syncs own transform to match the drone camera
# by looking up the DroneCamera node in the main scene each frame.

var drone_cam: Camera3D = null

func _process(_delta: float) -> void:
	if drone_cam == null:
		# walk up to root then find DroneCamera in the main scene
		drone_cam = get_tree().root.get_node_or_null(
			"DroneWorld/Drone/CameraMount/DroneCamera"
		)
		return
	# copy transform directly — we are inside the SubViewport so 'transform'
	# here is our local (and only) transform; set it to the drone cam's world transform
	global_transform = drone_cam.global_transform
