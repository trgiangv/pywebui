param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $PSScriptRoot 'deps/DepsSync.csproj'
$bin = Join-Path $root 'pywebui/bin'

dotnet build $project -c $Configuration

$required = @(
    'Microsoft.Web.WebView2.Core.dll',
    'Microsoft.Web.WebView2.Wpf.dll',
    'Microsoft.Web.WebView2.WinForms.dll',
    'Revit.Async.dll',
    'Newtonsoft.Json.dll'
)

foreach ($name in $required) {
    $path = Join-Path $bin $name
    if (-not (Test-Path $path)) {
        throw "Missing $name in $bin"
    }
}

$loader = Join-Path $bin 'runtimes/win-x64/native/WebView2Loader.dll'
if (-not (Test-Path $loader)) {
    throw "Missing WebView2Loader.dll at $loader"
}

Write-Host 'Shipped assemblies in pywebui/bin:'
Get-ChildItem $bin -Recurse -Filter '*.dll' | ForEach-Object {
    $relative = $_.FullName.Substring($bin.Length + 1)
    Write-Host ('  {0} ({1} bytes)' -f $relative, $_.Length)
}
