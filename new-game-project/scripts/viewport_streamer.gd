extends Node

# Streams SubViewport pixels over TCP after each rendered frame.
# Python side (godot_capture.py) connects and reads: 4B width, 4B height, RGBA bytes.

const PORT := 5006

@onready var viewport: SubViewport = $"../Drone/CameraViewport"

var server := TCPServer.new()
var client: StreamPeerTCP = null
var _streaming := false

func _ready() -> void:
	server.listen(PORT)
	print("[streamer] listening on TCP %d" % PORT)
	_stream_loop()

func _stream_loop() -> void:
	# wait several frames so the SubViewport has actually rendered
	for _i in 10:
		await get_tree().process_frame

	print("[streamer] viewport ready, streaming frames")
	while true:
		await RenderingServer.frame_post_draw

		# accept pending connection
		if server.is_connection_available():
			client = server.take_connection()
			print("[streamer] client connected")

		if client == null or client.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			continue

		if viewport == null:
			continue

		var img: Image = viewport.get_texture().get_image()
		if img == null or img.is_empty():
			continue

		img.convert(Image.FORMAT_RGBA8)
		var w := img.get_width()
		var h := img.get_height()
		if w == 0 or h == 0:
			continue

		var header := PackedByteArray()
		header.resize(8)
		header.encode_u32(0, w)
		header.encode_u32(4, h)

		if client.put_data(header) != OK or client.put_data(img.get_data()) != OK:
			print("[streamer] client disconnected")
			client = null
