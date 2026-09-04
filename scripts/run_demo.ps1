param([string]$Blender = "D:\Program Files\blender-5.2.1-windows-x64\blender.exe", [switch]$ShowWindow)
$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Project "src"
$Scene = Join-Path $Project "examples\desktop.scene.json"
$IR = Join-Path $Project "build\desktop.ir.json"
$Blend = Join-Path $Project "build\desktop.blend"
python -m digital_twin.compiler $Scene $IR
if ($LASTEXITCODE -ne 0) { throw "Compiler failed" }
$BlenderArgs = @()
if (-not $ShowWindow) { $BlenderArgs += "--background" }
$BlenderArgs += @("--factory-startup", "--python", (Join-Path $Project "blender\executor.py"), "--", "--input", $IR, "--output", $Blend, "--clear-scene")
& $Blender @BlenderArgs
if ($LASTEXITCODE -ne 0) { throw "Blender executor failed" }
Write-Host "Demo complete: $Blend"
