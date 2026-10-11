extends ColorRect

@export var speed := 120.0

var movement_enabled := true
var world_bounds := Rect2(0.0, 0.0, 640.0, 360.0)
var obstacles: Array[Rect2] = []


func _physics_process(delta: float) -> void:
	if not movement_enabled:
		return
	var direction := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	direction += Vector2(
		float(Input.is_key_pressed(KEY_D)) - float(Input.is_key_pressed(KEY_A)),
		float(Input.is_key_pressed(KEY_S)) - float(Input.is_key_pressed(KEY_W))
	)
	if direction.length_squared() > 1.0:
		direction = direction.normalized()
	_move_with_collisions(direction * speed * delta)


func configure(bounds: Rect2, collision_rects: Array[Rect2]) -> void:
	world_bounds = bounds
	obstacles = collision_rects
	position = _clamp_to_bounds(position)


func world_rect() -> Rect2:
	return Rect2(position, size)


func _move_with_collisions(motion: Vector2) -> void:
	var candidate := position
	candidate.x += motion.x
	candidate = _clamp_to_bounds(candidate)
	if not _collides(Rect2(candidate, size)):
		position.x = candidate.x

	candidate = position
	candidate.y += motion.y
	candidate = _clamp_to_bounds(candidate)
	if not _collides(Rect2(candidate, size)):
		position.y = candidate.y


func _clamp_to_bounds(candidate: Vector2) -> Vector2:
	return Vector2(
		clampf(candidate.x, world_bounds.position.x, world_bounds.end.x - size.x),
		clampf(candidate.y, world_bounds.position.y, world_bounds.end.y - size.y)
	)


func _collides(rect: Rect2) -> bool:
	for obstacle in obstacles:
		if rect.intersects(obstacle):
			return true
	return false
