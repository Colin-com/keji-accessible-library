# 开发与构建

以下命令均在仓库根目录执行，并使用 console 版 Godot，以便获得清晰的命令行输出。

## Headless 导入

```powershell
.\.tools\godot\Godot_v4.7.2-stable_win64_console.exe --headless --path . --import
```

## 导出 Web

一键导入并导出：

```powershell
.\scripts\build_web.ps1
```

也可以单独执行导出命令：

```powershell
.\.tools\godot\Godot_v4.7.2-stable_win64_console.exe --headless --path . --export-release "Web" exports/web/index.html
```

如需使用其他位置的 Godot，先设置环境变量：

```powershell
$env:GODOT_BIN = "C:\path\to\Godot_console.exe"
.\scripts\build_web.ps1
```

## 本地预览

浏览器不能可靠地通过 `file://` 直接运行 Godot Web 产物。请从导出目录启动静态服务器：

```powershell
cd exports\web
python -m http.server 8000
```

然后访问 `http://localhost:8000/`。

## 已知坑

- Web 导出依赖与 Godot 版本匹配的 export templates；缺失时导出会失败并提示安装模板。
- 必须使用 console 版可执行文件跑命令行任务，否则 Windows GUI 版不会提供同样清晰的 stdout。
- 当前 Web preset 已关闭线程支持，因此本地静态服务器无需额外配置 COOP/COEP 响应头。
- `.godot/` 是导入缓存，`exports/` 是构建产物；两者都不应提交到 Git。
