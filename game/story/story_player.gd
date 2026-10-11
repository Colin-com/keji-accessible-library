extends Node

signal node_changed(node: Dictionary)
signal ended(ending_id: String)
signal archive_unlocked(entry_id: String)

var state: Dictionary = {}

var _case_data: Dictionary = {}
var _current_id := ""
var _finished := true


func _ready() -> void:
	_reset_state()


func load_case(path: String) -> void:
	_reset_state()
	_case_data = {}
	_current_id = ""
	_finished = true

	if not FileAccess.file_exists(path):
		push_error("剧情文件不存在：%s" % path)
		return

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("无法读取剧情文件：%s" % path)
		return

	var json := JSON.new()
	var parse_error := json.parse(file.get_as_text())
	if parse_error != OK:
		push_error("剧情 JSON 解析失败：%s（第 %d 行：%s）" % [path, json.get_error_line(), json.get_error_message()])
		return
	if not json.data is Dictionary:
		push_error("剧情文件根节点必须是对象：%s" % path)
		return

	_case_data = json.data
	var start_id := str(_case_data.get("start", ""))
	if start_id.is_empty():
		push_error("剧情缺少 start：%s" % path)
		return

	_finished = false
	goto(start_id)


func current() -> Dictionary:
	if _current_id.is_empty():
		return {}
	var nodes: Dictionary = _case_data.get("nodes", {})
	var node: Variant = nodes.get(_current_id, {})
	return node if node is Dictionary else {}


func visible_options() -> Array:
	var node := current()
	if str(node.get("type", "")) != "choice":
		return []

	var visible: Array = []
	var options: Variant = node.get("options", [])
	if not options is Array:
		return visible
	for option_value: Variant in options:
		if option_value is Dictionary and _requirements_met(option_value.get("require", {})):
			visible.append(option_value)
	return visible


func choose(i: int) -> void:
	if _finished:
		return
	var options := visible_options()
	if i < 0 or i >= options.size():
		push_warning("选项索引越界：%d" % i)
		return
	var option: Dictionary = options[i]
	_apply_effects(option)
	var next_id := str(option.get("next", ""))
	if next_id.is_empty():
		_finish("")
		return
	goto(next_id)


func advance() -> void:
	if _finished:
		return
	var node := current()
	if str(node.get("type", "")) != "say":
		return
	var next_id := str(node.get("next", ""))
	if next_id.is_empty():
		_finish("")
		return
	goto(next_id)


func goto(node_id: String) -> void:
	var nodes: Dictionary = _case_data.get("nodes", {})
	if not nodes.has(node_id) or not nodes[node_id] is Dictionary:
		push_error("剧情节点不存在：%s" % node_id)
		_finish("")
		return

	_current_id = node_id
	_finished = false
	var node: Dictionary = nodes[node_id]
	_apply_effects(node)

	if str(node.get("type", "")) == "choice" and visible_options().is_empty():
		var fallback_id := str(node.get("fallback_next", ""))
		if fallback_id.is_empty():
			push_error("选择节点没有可见选项且缺少 fallback_next：%s" % node_id)
			_finish("")
			return
		goto(fallback_id)
		return

	node_changed.emit(node.duplicate(true))
	if str(node.get("type", "")) == "end":
		_finish(str(node.get("ending_id", "")))


func has_story_node(node_id: String) -> bool:
	var nodes: Dictionary = _case_data.get("nodes", {})
	return nodes.has(node_id) and nodes[node_id] is Dictionary


func current_node_id() -> String:
	return _current_id


func is_finished() -> bool:
	return _finished


func _reset_state() -> void:
	state = {
		"flags": {},
		"relation": {},
		"progress": 0,
		"unlocked": []
	}


func _requirements_met(requirements: Variant) -> bool:
	if not requirements is Dictionary:
		return true
	var flags: Dictionary = state["flags"]
	for flag_name: Variant in requirements:
		if flags.get(str(flag_name), false) != requirements[flag_name]:
			return false
	return true


func _apply_effects(source: Dictionary) -> void:
	var flag_changes: Variant = source.get("set", {})
	if flag_changes is Dictionary:
		var flags: Dictionary = state["flags"]
		for flag_name: Variant in flag_changes:
			flags[str(flag_name)] = flag_changes[flag_name]

	var relation_changes: Variant = source.get("relation", {})
	if relation_changes is Dictionary:
		var relations: Dictionary = state["relation"]
		for relation_name: Variant in relation_changes:
			var key := str(relation_name)
			relations[key] = int(relations.get(key, 0)) + int(relation_changes[relation_name])

	state["progress"] = int(state["progress"]) + int(source.get("progress", 0))

	var unlocks: Variant = source.get("unlock", [])
	if unlocks is Array:
		var unlocked: Array = state["unlocked"]
		for entry_value: Variant in unlocks:
			var entry_id := str(entry_value)
			if not unlocked.has(entry_id):
				unlocked.append(entry_id)
				archive_unlocked.emit(entry_id)


func _finish(ending_id: String) -> void:
	if _finished:
		return
	_finished = true
	ended.emit(ending_id)
