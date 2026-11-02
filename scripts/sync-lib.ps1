param(
    [string]$Destination = (Join-Path $env:APPDATA 'pyRevit\Extensions\pywebui.lib')
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$package = Join-Path $root 'pywebui'

if (-not (Test-Path -LiteralPath $package)) {
    throw "Missing package at $package"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$copied = 0
$unchanged = 0

function Copy-One {
    param(
        [string]$Source,
        [string]$Relative
    )
    $target = Join-Path $Destination $Relative
    if ((Test-Path -LiteralPath $target) -and
        ((Get-FileHash -LiteralPath $Source).Hash -eq (Get-FileHash -LiteralPath $target).Hash)) {
        $script:unchanged++
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $target -Force
    $script:copied++
}

Copy-One (Join-Path $root 'extension.json') 'extension.json'

Get-ChildItem -LiteralPath $package -Recurse -File | ForEach-Object {
    if ($_.FullName -match '\\__pycache__\\' -or $_.Extension -in '.pyc', '.pyo') {
        return
    }
    $relative = $_.FullName.Substring($root.Length).TrimStart('\')
    Copy-One $_.FullName $relative
}

Write-Host ("Copied {0} file(s), {1} unchanged, to {2}" -f $copied, $unchanged, $Destination)
