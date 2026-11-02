[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FlowRoot,
    [ValidateSet('Normal', 'FullScreen')][string]$Layout = 'FullScreen'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or later is required.' }

$root = (Resolve-Path -LiteralPath $FlowRoot).Path
$exe = Join-Path $root 'Flow.Launcher.exe'
$runtimePath = Join-Path $root 'Flow.Launcher.runtimeconfig.json'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or
    -not (Test-Path -LiteralPath $runtimePath -PathType Leaf)) {
    throw 'FlowRoot must contain Flow.Launcher.exe and its runtimeconfig.json.'
}
foreach ($process in @(Get-Process -Name 'Flow.Launcher' -ErrorAction SilentlyContinue)) {
    if ($process.Path -eq $exe) { throw 'Close this Flow Launcher instance before configuring it.' }
}

$portableData = Join-Path $root 'UserData'
$dataRoot = if (Test-Path -LiteralPath $portableData -PathType Container) {
    $portableData
} else {
    Join-Path $env:APPDATA 'FlowLauncher'
}
$settingsPath = Join-Path $dataRoot 'Settings\Settings.json'
if (-not (Test-Path -LiteralPath $settingsPath -PathType Leaf)) {
    throw 'Start Flow Launcher once to create its settings, then close it and rerun this script.'
}
$settings = [System.Text.Json.Nodes.JsonNode]::Parse([IO.File]::ReadAllText($settingsPath))
$runtime = [System.Text.Json.Nodes.JsonNode]::Parse([IO.File]::ReadAllText($runtimePath))
if ($null -eq $runtime['runtimeOptions'] -or $null -eq $runtime['runtimeOptions']['configProperties']) {
    throw 'Unexpected runtime configuration: runtimeOptions.configProperties is missing.'
}

$themeName = if ($Layout -eq 'FullScreen') { 'AMOLED-HighContrast-FullScreen' } else { 'AMOLED-HighContrast' }
$settings['Theme'] = [System.Text.Json.Nodes.JsonValue]::Create($themeName)
$settings['ColorScheme'] = [System.Text.Json.Nodes.JsonValue]::Create('Dark')
if ($Layout -eq 'FullScreen') {
    Add-Type -AssemblyName PresentationFramework
    $area = [System.Windows.SystemParameters]::WorkArea
    $width = [Math]::Max(400, [Math]::Floor($area.Width))
    $itemHeight = if ($null -ne $settings['ItemHeightSize']) { [double]$settings['ItemHeightSize'].ToString() } else { 58 }
    if ($itemHeight -le 0) { throw 'The configured result item height is invalid.' }
    $maxResults = [Math]::Clamp([int][Math]::Floor(($area.Height - 60) / $itemHeight), 2, 17)
    $settings['WindowSize'] = [System.Text.Json.Nodes.JsonValue]::Create([double]$width)
    $settings['SearchWindowAlign'] = [System.Text.Json.Nodes.JsonValue]::Create('Custom')
    $settings['CustomWindowLeft'] = [System.Text.Json.Nodes.JsonValue]::Create([double]0)
    $settings['CustomWindowTop'] = [System.Text.Json.Nodes.JsonValue]::Create([double]0)
    $settings['UseDropShadowEffect'] = [System.Text.Json.Nodes.JsonValue]::Create($false)
    $settings['MaxResultsToShow'] = [System.Text.Json.Nodes.JsonValue]::Create($maxResults)
}
$runtime['runtimeOptions']['configProperties']['Switch.System.Windows.Controls.Text.UseAdornerForTextboxSelectionRendering'] =
    [System.Text.Json.Nodes.JsonValue]::Create($false)

$backupSuffix = '.before-amoled-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.bak'
Copy-Item -LiteralPath $settingsPath -Destination ($settingsPath + $backupSuffix)
Copy-Item -LiteralPath $runtimePath -Destination ($runtimePath + $backupSuffix)
$themeDirectory = Join-Path $dataRoot 'Themes'
[void][IO.Directory]::CreateDirectory($themeDirectory)
$themeSource = Join-Path $PSScriptRoot "..\adapters\flow-launcher\$themeName.xaml"
Copy-Item -LiteralPath $themeSource -Destination (Join-Path $themeDirectory "$themeName.xaml") -Force
$options = [System.Text.Json.JsonSerializerOptions]::new()
$options.WriteIndented = $true
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($settingsPath, $settings.ToJsonString($options), $utf8)
[IO.File]::WriteAllText($runtimePath, $runtime.ToJsonString($options), $utf8)
Write-Output "Configured $themeName. Restart Flow Launcher to apply it."
