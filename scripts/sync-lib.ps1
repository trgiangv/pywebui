param(
    [string]$Destination = (Join-Path $env:APPDATA 'pyRevit\Extensions\pyrevit_webview.lib')
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$package = Join-Path $root 'pyrevit_webview'

if (-not (Test-Path -LiteralPath $package)) {
    throw "Missing package at $package"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$copied = 0
$skipped = New-Object System.Collections.Generic.List[string]

function Copy-One {
    param(
        [string]$Source,
        [string]$Relative
    )
    $target = Join-Path $Destination $Relative
    $parent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    try {
        Copy-Item -LiteralPath $Source -Destination $target -Force -ErrorAction Stop
        $script:copied++
    }
    catch {
        $script:skipped.Add($Relative) | Out-Null
        Write-Warning ("skip {0}: {1}" -f $Relative, $_.Exception.Message)
    }
}

Copy-One (Join-Path $root 'extension.json') 'extension.json'

Get-ChildItem -LiteralPath $package -Recurse -File | ForEach-Object {
    if ($_.FullName -match '\\__pycache__\\' -or $_.Extension -in '.pyc', '.pyo') {
        return
    }
    $relative = $_.FullName.Substring($root.Length).TrimStart('\')
    Copy-One $_.FullName $relative
}

Write-Host ("Copied {0} file(s) to {1}" -f $copied, $Destination)
if ($skipped.Count -gt 0) {
    Write-Host ("Skipped {0} file(s):" -f $skipped.Count)
    $skipped | ForEach-Object { Write-Host ("  {0}" -f $_) }
}
