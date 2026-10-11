extends Node2D

const CASE_PATH := "res://game/data/case_library.json"
const DIALOGUE_SCENE := preload("res://scenes/dialogue_panel.tscn")
const ARCHIVE_SCENE_PATH := "res://scenes/archive_panel.tscn"

@onready var player = $Player
@onready var interactables: Node = $Interactables
@onready var status_label: Label = $Interface/Status

var _nearby_interactable: Area2D
var _dialogue
var _archive_panel: Node


func _ready() -> void:
	var obstacle_rects: Array[Rect2] = []
	for obstacle: Node in get_tree().get_nodes_in_group("obstacle"):
		if obstacle is Control:
			obstacle_rects.append(obstacle.get_global_rect())
	player.configure(Rect2(Vector2.ZERO, get_viewport_rect().size), obstacle_rects)

	if FileAccess.file_exists(CASE_PATH):
		Story.load_case(CASE_PATH)
		status_label.text = "靠近人物或公告板，按 E 交互　｜　Tab 档案库"
	else:
		status_label.text = "剧情数据准备中　｜　Tab 档案库"


func _process(_delta: float) -> void:
	_update_nearby_interactable()


func _input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	if event is InputEventKey and event.keycode == KEY_TAB:
		_toggle_archive()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.keycode == KEY_E and _dialogue == null and _nearby_interactable != null:
		_begin_interaction(_nearby_interactable)
		get_viewport().set_input_as_handled()


func _update_nearby_interactable() -> void:
	var nearest: Area2D
	var nearest_distance := INF
	for child: Node in interactables.get_children():
		if not child.has_method("is_player_near"):
			continue
		var is_near: bool = child.is_player_near(player.world_rect())
		var distance: float = player.position.distance_squared_to(child.global_position)
		if is_near and distance < nearest_distance:
			nearest = child
			nearest_distance = distance
	_nearby_interactable = nearest
	for child: Node in interactables.get_children():
		if child.has_method("set_prompt_visible"):
			child.set_prompt_visible(child == _nearby_interactable and _dialogue == null)


func _begin_interaction(interactable: Area2D) -> void:
	if interactable.node_id.is_empty():
		return
	if not Story.has_story_node(interactable.node_id):
		status_label.text = "剧情节点尚未就位：%s" % interactable.node_id
		return
	_dialogue = DIALOGUE_SCENE.instantiate()
	add_child(_dialogue)
	_dialogue.closed.connect(_on_dialogue_closed)
	player.movement_enabled = false
	if Story.current_node_id() != interactable.node_id or Story.is_finished():
		Story.goto(interactable.node_id)
	else:
		_dialogue.call_deferred("_render_node", Story.current())


func _on_dialogue_closed() -> void:
	_dialogue = null
	player.movement_enabled = true
	status_label.text = "靠近人物或公告板，按 E 交互　｜　Tab 档案库"


func _toggle_archive() -> void:
	if _archive_panel != null and is_instance_valid(_archive_panel):
		_archive_panel.queue_free()
		_archive_panel = null
		return
	if not ResourceLoader.exists(ARCHIVE_SCENE_PATH):
		status_label.text = "档案库界面尚未就位"
		return
	var archive_scene := load(ARCHIVE_SCENE_PATH) as PackedScene
	if archive_scene == null:
		status_label.text = "档案库界面无法载入"
		return
	_archive_panel = archive_scene.instantiate()
	add_child(_archive_panel)
