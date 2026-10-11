extends CanvasLayer

signal closed

@export_range(10.0, 120.0, 1.0) var characters_per_second := 42.0

@onready var panel: Panel = $Panel
@onready var speaker_label: Label = $Panel/Margin/Layout/Speaker
@onready var text_label: Label = $Panel/Margin/Layout/Text
@onready var options_box: VBoxContainer = $Panel/Margin/Layout/Options
@onready var hint_label: Label = $Panel/Margin/Layout/Hint

var _full_text := ""
var _shown_characters := 0.0
var _typing := false
var _option_buttons: Array[Button] = []
var _selected_option := 0


func _ready() -> void:
	Story.node_changed.connect(_on_node_changed)
	_render_node(Story.current())


func _process(delta: float) -> void:
	if not _typing:
		return
	_shown_characters = minf(_shown_characters + characters_per_second * delta, float(_full_text.length()))
	text_label.visible_characters = int(_shown_characters)
	if text_label.visible_characters >= _full_text.length():
		_finish_typing()


func _on_node_changed(node: Dictionary) -> void:
	_render_node(node)


func _unhandled_input(event: InputEvent) -> void:
	if not panel.visible or not event.is_pressed() or event.is_echo():
		return

	if event.is_action_pressed("ui_up") and not _option_buttons.is_empty():
		_select_option(posmod(_selected_option - 1, _option_buttons.size()))
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("ui_down") and not _option_buttons.is_empty():
		_select_option((_selected_option + 1) % _option_buttons.size())
		get_viewport().set_input_as_handled()
		return

	var number_index := _number_key_index(event)
	if number_index >= 0 and number_index < _option_buttons.size():
		_activate_option(number_index)
		get_viewport().set_input_as_handled()
		return

	if event.is_action_pressed("ui_accept"):
		if _typing:
			_reveal_all()
		elif not _option_buttons.is_empty():
			_activate_option(_selected_option)
		else:
			_continue_dialogue()
		get_viewport().set_input_as_handled()


func _render_node(node: Dictionary) -> void:
	_clear_options()
	if node.is_empty():
		_close()
		return

	var node_type := str(node.get("type", ""))
	match node_type:
		"say":
			speaker_label.text = str(node.get("speaker", ""))
			_start_typing(str(node.get("text", "")))
			hint_label.text = "回车键继续"
		"choice":
			speaker_label.text = "做出选择"
			_start_typing(str(node.get("prompt", "")))
			_build_options(Story.visible_options())
			hint_label.text = "↑↓ 选择　回车键确认　数字键直达"
		"end":
			speaker_label.text = str(node.get("title", "结局"))
			_start_typing(str(node.get("text", "")))
			hint_label.text = "回车键返回图书馆"
		_:
			speaker_label.text = "剧情数据错误"
			_start_typing("无法显示这个剧情节点。")
			hint_label.text = "回车键返回图书馆"


func _start_typing(value: String) -> void:
	_full_text = value
	text_label.text = value
	text_label.visible_characters = 0
	_shown_characters = 0.0
	_typing = not value.is_empty()
	if not _typing:
		_finish_typing()


func _finish_typing() -> void:
	_typing = false
	text_label.visible_characters = -1
	if not _option_buttons.is_empty():
		_select_option(_selected_option)


func _reveal_all() -> void:
	_shown_characters = float(_full_text.length())
	_finish_typing()


func _build_options(options: Array) -> void:
	for i in options.size():
		var option: Dictionary = options[i]
		var button := Button.new()
		button.text = "%d. %s" % [i + 1, str(option.get("text", ""))]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.focus_mode = Control.FOCUS_ALL
		button.pressed.connect(_activate_option.bind(i))
		button.mouse_entered.connect(_select_option.bind(i))
		options_box.add_child(button)
		_option_buttons.append(button)
	_selected_option = 0


func _clear_options() -> void:
	for button in _option_buttons:
		button.queue_free()
	_option_buttons.clear()
	_selected_option = 0


func _select_option(index: int) -> void:
	if index < 0 or index >= _option_buttons.size():
		return
	_selected_option = index
	_option_buttons[index].grab_focus()


func _activate_option(index: int) -> void:
	if _typing:
		_reveal_all()
		return
	Story.choose(index)


func _continue_dialogue() -> void:
	var node_type := str(Story.current().get("type", ""))
	if node_type == "say" and not Story.is_finished():
		Story.advance()
	else:
		_close()


func _close() -> void:
	closed.emit()
	queue_free()


func _number_key_index(event: InputEvent) -> int:
	if not event is InputEventKey:
		return -1
	match event.keycode:
		KEY_1, KEY_KP_1:
			return 0
		KEY_2, KEY_KP_2:
			return 1
		KEY_3, KEY_KP_3:
			return 2
	return -1
