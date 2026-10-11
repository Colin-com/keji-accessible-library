extends Area2D

@export var display_name := "交互点"
@export var node_id := ""

@onready var prompt: Label = $Prompt
@onready var collision_shape: CollisionShape2D = $CollisionShape2D


func _ready() -> void:
	prompt.visible = false


func set_prompt_visible(value: bool) -> void:
	prompt.visible = value
	if value:
		prompt.text = "%s　按 E 交互" % display_name


func is_player_near(player_rect: Rect2) -> bool:
	var rectangle := collision_shape.shape as RectangleShape2D
	if rectangle == null:
		return false
	var area_rect := Rect2(global_position - rectangle.size * 0.5, rectangle.size)
	return area_rect.intersects(player_rect)
