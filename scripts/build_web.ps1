$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$defaultGodot = "E:\Claw-Data\pixel-sci-game\.tools\godot\Godot_v4.7.2-stable_win64_console.exe"
$godotBin = if ([string]::IsNullOrWhiteSpace($env:GODOT_BIN)) {
    $defaultGodot
} else {
    $env:GODOT_BIN
}

if (-not (Test-Path -LiteralPath $godotBin -PathType Leaf)) {
    Write-Error "找不到 Godot 控制台程序：$godotBin"
    exit 1
}

Write-Host "正在执行 Godot headless 导入……"
& $godotBin --headless --path $repoRoot --import
if ($LASTEXITCODE -ne 0) {
    Write-Error "Godot headless 导入失败，退出码：$LASTEXITCODE"
    exit 1
}

$webOutputDir = Join-Path $repoRoot "exports\web"
New-Item -ItemType Directory -Force -Path $webOutputDir | Out-Null

Write-Host "正在导出 Web 版本……"
& $godotBin --headless --path $repoRoot --export-release "Web" "exports/web/index.html"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Godot Web 导出失败，退出码：$LASTEXITCODE"
    exit 1
}

$indexPath = Join-Path $webOutputDir "index.html"
if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
    Write-Error "Godot 命令执行成功，但未生成预期产物：$indexPath"
    exit 1
}

$artifact = Get-Item -LiteralPath $indexPath
Write-Host ("Web 导出成功：{0}（{1:N0} 字节）" -f $artifact.FullName, $artifact.Length)
