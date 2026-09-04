param([string]$Blender = "D:\Program Files\blender-5.2.1-windows-x64\blender.exe")
$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent $PSScriptRoot
$Web = Join-Path $Project "web"
$Assets = Join-Path $Web "public\assets"
New-Item -ItemType Directory -Path $Assets -Force | Out-Null
& $Blender --background (Join-Path $Project "build\server-room-l4.blend") --python (Join-Path $Project "blender\export_web.py") -- --glb (Join-Path $Assets "server-room.glb") --manifest (Join-Path $Assets "scene-manifest.json")
if ($LASTEXITCODE -ne 0) { throw "Blender web export failed" }
Push-Location $Web
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Web build failed" }
} finally { Pop-Location }
Write-Host "Web MVP ready. Run: cd web; npm start"
