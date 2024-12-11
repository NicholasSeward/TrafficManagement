extends Node3D

# Parameters for the sphere
@export var radius: float = 100.0
var target_position: Vector3
var speed: Vector3 = Vector3.ZERO

func _ready():
	# Create a new SphereMesh and set its parameters
	var sphere_mesh = SphereMesh.new()
	sphere_mesh.radius = radius
	sphere_mesh.height = radius*2
	$MeshInstance3D.mesh = sphere_mesh
	
	# Create a unique material for this sphere instance
	var original_material = $MeshInstance3D.material_override
	var unique_material = StandardMaterial3D.new()
	$MeshInstance3D.material_override = unique_material
	if original_material:
		unique_material = original_material.duplicate()
		$MeshInstance3D.material_override = unique_material
	# Set a random color
	unique_material.albedo_color = Color(randf(), randf(), randf())  # Random RGB color

	# Adjust shading mode if needed
	unique_material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL

# Function to set a new target position
func set_new_target_position(new_position):
	target_position = new_position
	var distance = target_position - global_transform.origin
	speed = distance / 5  # Calculate speed to reach in 10 frames
	print("Target position:", target_position, "Speed:", speed)
	
# Function to update the sphere's position each frame
func _process(delta: float):
	var current_position = global_transform.origin
	var distance_to_target = target_position - current_position

	# Move the sphere towards the target position
	if distance_to_target.length() > speed.length():
		global_transform.origin += speed
	else:
		# Snap to target when close enough
		global_transform.origin = target_position
		speed = Vector3.ZERO  # Stop movement
