extends Node3D

# Path to your SQLite database
const DB_PATH = "res://db/roads.db"

# Store intersections and road data
var intersections = {}
var roads = []
# Dictionary to store spheres, keyed by their IDs
var spheres = {}
const SPHERE_SCENE = preload("res://sphere.tscn")
# URL of the endpoint
const API_URL = "http://127.0.0.1:9999/cars/updated_recently"

# Timer to periodically fetch and update data
@onready var update_timer = Timer.new()

func _ready():
	load_data_from_db()
	create_road_meshes()
	
	# Add and configure the timer
	add_child(update_timer)
	update_timer.wait_time = 1.0/30  # Fetch every second
	update_timer.one_shot = false
	update_timer.connect("timeout", _fetch_and_update)
	update_timer.start()
	
	# Fetch and update immediately on start
	_fetch_and_update()


func _fetch_and_update():
	var http_request = HTTPRequest.new()
	add_child(http_request)

	http_request.connect("request_completed",_on_request_completed)
	http_request.request(API_URL)

func _on_request_completed(result, response_code, headers, body):
	if response_code == 200:
		var json = JSON.new()
		var error = json.parse(body.get_string_from_utf8())
		if error == OK:
			_update_spheres(json.data)

func _update_spheres(data):
	# Extract IDs from the JSON
	var new_ids=[]
	for car in data:
		new_ids.append(car["id"])
	#var new_ids=[car["id"] for car in data]
	#var new_ids = data.map(lambda car: car["id"])
	
	# Remove spheres that are no longer present in the JSON
	for id in spheres.keys():
		if id not in new_ids:
			if spheres.has(id):
				spheres[id].queue_free()
				spheres.erase(id)

	# Update or create spheres based on JSON data
	for car in data:
		var id = car["id"]
		var x = car["x"]
		var y = car["y"]
		var position = Vector3(x, 0, y)  # Assume z = 0 for simplicity

		if spheres.has(id):
			# Update the existing sphere's position
			spheres[id].set_new_target_position(position)
		else:
			# Create a new sphere from the Sphere.tscn
			var sphere_instance = SPHERE_SCENE.instantiate()

			# Set the sphere's parameters
			sphere_instance.radius = 3.0  # Default radius
			sphere_instance.position = position

			# Add the sphere to the scene
			add_child(sphere_instance)
			spheres[id] = sphere_instance
# Step 1: Load intersections and roads from the database
func load_data_from_db():
	var db = SQLite.new()
	db.path = DB_PATH
	db.open_db()

	# Load intersections
	db.query("SELECT id, x, y FROM intersections")
	for row in db.query_result:
		#print(row)
		intersections[row["id"]] = {
			"id": row["id"],
			"x": row["x"],
			"y": row["y"]
		}

	# Load roads
	db.query("SELECT id, intersection_id1, intersection_id2 FROM roads")
	for row in db.query_result:
		roads.append({
			"id": row["id"],
			"intersection_id1": row["intersection_id1"],
			"intersection_id2": row["intersection_id2"]
		})

	db.close_db()
	print("Loaded intersections and roads.")

# Step 2: Create MeshInstance3D nodes for roads
func create_road_meshes():
	var road_width = 2.0  # Width of the road
	var road_height = 0.1  # Thickness of the road
	var road_color = Color(0.5, 0.5, 0.5)

	# Create a material for the roads
	var road_material = StandardMaterial3D.new()
	road_material.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL
	road_material.albedo_color = road_color
	for id in intersections:
		var intersection=intersections[id]
		var point = Vector3(intersection["x"], 0, intersection["y"])
		# Create a QuadMesh for the road
		var mesh=SphereMesh.new()
		mesh.radius=road_width/2*1.5;
		mesh.height=road_width*1.5;
		#mesh.size=Vector3((point1-point2).length(),1,road_width)

		# Create MeshInstance3D and assign the quad mesh
		var road_mesh_instance = MeshInstance3D.new()
		road_mesh_instance.position=point
		road_mesh_instance.mesh = mesh
		road_mesh_instance.material_override = road_material

		# Add the MeshInstance3D to the scene tree
		add_child(road_mesh_instance)

	for road in roads:
		var id1 = road["intersection_id1"]
		var id2 = road["intersection_id2"]

		# Find the intersections by ID
		var intersection1 = intersections[id1]
		var intersection2 = intersections[id2]

		if intersection1 and intersection2:
			# Get coordinates
			var point1 = Vector3(intersection1["x"], 0, intersection1["y"])
			var point2 = Vector3(intersection2["x"], 0, intersection2["y"])

			# Calculate the vector perpendicular to the road in the XZ plane
			var direction = (point2 - point1).normalized()
			var perpendicular = Vector3(-direction.z, 0, direction.x) * (road_width / 2)

			# Define quad vertices
			var vertices = [
				point1 - perpendicular,
				point1 + perpendicular,
				point2 + perpendicular,
				point2 - perpendicular
			]
			print(vertices)

			# Create a QuadMesh for the road
			var mesh=CylinderMesh.new()
			mesh.bottom_radius=road_width/2
			mesh.top_radius=road_width/2
			mesh.height=(point1-point2).length()
			#mesh.size=Vector3((point1-point2).length(),1,road_width)

			# Create MeshInstance3D and assign the quad mesh
			var road_mesh_instance = MeshInstance3D.new()
			road_mesh_instance.position=(point1+point2)/2
			var d=Vector3(1,0,0).signed_angle_to((point1-point2),Vector3(0,1,0))
			road_mesh_instance.rotate_z(PI/2)
			road_mesh_instance.rotate_y(d)
			road_mesh_instance.mesh = mesh
			road_mesh_instance.material_override = road_material

			# Add the MeshInstance3D to the scene tree
			add_child(road_mesh_instance)

			print("Added road mesh between points:", point1, point2)

	print("All road meshes created.")
