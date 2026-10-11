extends Node

const OFFICIAL_CASE := "res://game/data/case_library.json"
const FIXTURE_CASE := "res://tests/fixture_case.json"
const MAX_PATH_DEPTH := 256

var _case_data: Dictionary = {}
var _failures: PackedStringArray = []
var _ending_ids: Dictionary = {}
var _completed_paths := 0


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var path := OFFICIAL_CASE if FileAccess.file_exists(OFFICIAL_CASE) else FIXTURE_CASE
	print("=== 剧情路径测试 ===")
	print("数据文件：%s" % path)
	_case_data = _read_case(path)
	if _case_data.is_empty():
		_finish_test()
		return

	_validate_graph()
	if _failures.is_empty():
		var initial_state := {"flags": {}, "relation": {}, "progress": 0, "unlocked": []}
		_walk(str(_case_data.get("start", "")), initial_state, PackedStringArray(), {}, 0)

	_smoke_test_runtime(path)
	_finish_test()


func _read_case(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		_failures.append("无法读取数据文件：%s" % path)
		return {}
	var json := JSON.new()
	var error := json.parse(file.get_as_text())
	if error != OK:
		_failures.append("JSON 解析失败（第 %d 行）：%s" % [json.get_error_line(), json.get_error_message()])
		return {}
	if not json.data is Dictionary:
		_failures.append("数据根节点不是对象")
		return {}
	return json.data


func _validate_graph() -> void:
	var nodes: Variant = _case_data.get("nodes", {})
	if not nodes is Dictionary or nodes.is_empty():
		_failures.append("nodes 缺失或为空")
		return
	var start_id := str(_case_data.get("start", ""))
	if not nodes.has(start_id):
		_failures.append("start 指向不存在的节点：%s" % start_id)

	for node_id_value: Variant in nodes:
		var node_id := str(node_id_value)
		var node_value: Variant = nodes[node_id_value]
		if not node_value is Dictionary:
			_failures.append("节点不是对象：%s" % node_id)
			continue
		var node: Dictionary = node_value
		var node_type := str(node.get("type", ""))
		if node_type not in ["say", "choice", "end"]:
			_failures.append("节点类型非法：%s -> %s" % [node_id, node_type])
			continue
		if node.has("next"):
			_validate_reference(node_id, "next", str(node.get("next", "")), nodes)
		if node.has("fallback_next"):
			_validate_reference(node_id, "fallback_next", str(node.get("fallback_next", "")), nodes)
		if node_type == "choice":
			var options: Variant = node.get("options", [])
			if not options is Array:
				_failures.append("选择节点 options 不是数组：%s" % node_id)
				continue
			for option_index in options.size():
				var option_value: Variant = options[option_index]
				if not option_value is Dictionary:
					_failures.append("选项不是对象：%s[%d]" % [node_id, option_index])
					continue
				var next_id := str(option_value.get("next", ""))
				_validate_reference("%s[%d]" % [node_id, option_index], "next", next_id, nodes)


func _validate_reference(owner: String, field: String, target: String, nodes: Dictionary) -> void:
	if target.is_empty() or not nodes.has(target):
		_failures.append("悬空引用：%s.%s -> %s" % [owner, field, target if not target.is_empty() else "<空>"])


func _walk(node_id: String, incoming_state: Dictionary, path: PackedStringArray, seen: Dictionary, depth: int) -> void:
	var trace := path.duplicate()
	trace.append(node_id)
	if depth > MAX_PATH_DEPTH:
		_failures.append("路径超过 %d 步，疑似循环：%s" % [MAX_PATH_DEPTH, " -> ".join(trace)])
		return

	var nodes: Dictionary = _case_data.get("nodes", {})
	if not nodes.has(node_id):
		_failures.append("路径遇到不存在的节点：%s" % " -> ".join(trace))
		return
	var node: Dictionary = nodes[node_id]
	var next_state: Dictionary = incoming_state.duplicate(true)
	_apply_effects(node, next_state)

	var signature := "%s|%s" % [node_id, JSON.stringify(next_state)]
	if seen.has(signature):
		_failures.append("路径形成循环：%s" % " -> ".join(trace))
		return
	var next_seen := seen.duplicate()
	next_seen[signature] = true

	match str(node.get("type", "")):
		"end":
			var ending_id := str(node.get("ending_id", ""))
			if ending_id.is_empty():
				_failures.append("结局缺少 ending_id：%s" % " -> ".join(trace))
				return
			_ending_ids[ending_id] = true
			_completed_paths += 1
			print("路径通过：%s => %s" % [" -> ".join(trace), ending_id])
		"say":
			var next_id := str(node.get("next", ""))
			if next_id.is_empty():
				_failures.append("路径未抵达 end 就结束：%s" % " -> ".join(trace))
			else:
				_walk(next_id, next_state, trace, next_seen, depth + 1)
		"choice":
			var visible := _visible_options(node, next_state)
			if visible.is_empty():
				var fallback_id := str(node.get("fallback_next", ""))
				if fallback_id.is_empty():
					_failures.append("选项全部被过滤且无 fallback_next：%s" % " -> ".join(trace))
				else:
					var fallback_trace := trace.duplicate()
					fallback_trace.append("[fallback]")
					_walk(fallback_id, next_state, fallback_trace, next_seen, depth + 1)
				return
			for option_value: Variant in visible:
				var option: Dictionary = option_value
				var option_state := next_state.duplicate(true)
				_apply_effects(option, option_state)
				var option_trace := trace.duplicate()
				option_trace.append("[%s]" % str(option.get("text", "")))
				_walk(str(option.get("next", "")), option_state, option_trace, next_seen, depth + 1)


func _visible_options(node: Dictionary, state: Dictionary) -> Array:
	var result: Array = []
	var options: Array = node.get("options", [])
	for option_value: Variant in options:
		if not option_value is Dictionary:
			continue
		var requirements: Variant = option_value.get("require", {})
		var allowed := true
		if requirements is Dictionary:
			var flags: Dictionary = state["flags"]
			for flag_name: Variant in requirements:
				if flags.get(str(flag_name), false) != requirements[flag_name]:
					allowed = false
					break
		if allowed:
			result.append(option_value)
	return result


func _apply_effects(source: Dictionary, state: Dictionary) -> void:
	var sets: Variant = source.get("set", {})
	if sets is Dictionary:
		for key: Variant in sets:
			state["flags"][str(key)] = sets[key]
	var relations: Variant = source.get("relation", {})
	if relations is Dictionary:
		for key: Variant in relations:
			var relation_key := str(key)
			state["relation"][relation_key] = int(state["relation"].get(relation_key, 0)) + int(relations[key])
	state["progress"] = int(state["progress"]) + int(source.get("progress", 0))
	var unlocks: Variant = source.get("unlock", [])
	if unlocks is Array:
		for entry: Variant in unlocks:
			if not state["unlocked"].has(str(entry)):
				state["unlocked"].append(str(entry))


func _smoke_test_runtime(path: String) -> void:
	Story.load_case(path)
	if Story.current().is_empty():
		_failures.append("Story.load_case 后 current() 为空")
	for required_key in ["flags", "relation", "progress", "unlocked"]:
		if not Story.state.has(required_key):
			_failures.append("Story.state 缺少键：%s" % required_key)


func _finish_test() -> void:
	if _ending_ids.size() < 2:
		_failures.append("可达 ending_id 少于 2 个，实际：%s" % ", ".join(_ending_ids.keys()))
	print("检查节点数：%d" % (_case_data.get("nodes", {}) as Dictionary).size())
	print("完成路径数：%d" % _completed_paths)
	print("可达结局：%s" % ", ".join(_ending_ids.keys()))
	if _failures.is_empty():
		print("测试通过：所有路径抵达 end；无悬空 next；至少两个结局可达；无过滤死节点。")
		get_tree().quit(0)
		return
	print("测试失败（%d 项）：" % _failures.size())
	for failure in _failures:
		printerr("- %s" % failure)
	get_tree().quit(1)
