$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$base = Join-Path $repo '.test-fixtures'
[void][IO.Directory]::CreateDirectory($base)
$fixture = Join-Path $base ([Guid]::NewGuid().ToString('N'))
$baseFull = [IO.Path]::GetFullPath($base).TrimEnd('\') + '\'
$fixtureFull = [IO.Path]::GetFullPath($fixture)
if (-not $fixtureFull.StartsWith($baseFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The test fixture is outside its expected directory.'
}

try {
    $settingsDir = Join-Path $fixtureFull 'UserData\Settings'
    [void][IO.Directory]::CreateDirectory($settingsDir)
    [IO.File]::WriteAllText((Join-Path $fixtureFull 'Flow.Launcher.exe'), 'fixture')
    [IO.File]::WriteAllText((Join-Path $fixtureFull 'Flow.Launcher.runtimeconfig.json'), '{"runtimeOptions":{"configProperties":{"ExistingOption":true}}}')
    [IO.File]::WriteAllText((Join-Path $settingsDir 'Settings.json'), '{"Theme":"old","ColorScheme":"System","WindowSize":580,"ItemHeightSize":58,"SearchWindowAlign":"Center","UseDropShadowEffect":true,"MaxResultsToShow":5,"KeepThis":"unchanged"}')
    & (Join-Path $PSScriptRoot 'configure-flow-launcher.ps1') -FlowRoot $fixtureFull -Layout FullScreen
    $settings = Get-Content (Join-Path $settingsDir 'Settings.json') -Raw | ConvertFrom-Json
    $runtime = Get-Content (Join-Path $fixtureFull 'Flow.Launcher.runtimeconfig.json') -Raw | ConvertFrom-Json
    Add-Type -AssemblyName PresentationFramework
    $expectedWidth = [Math]::Max(400, [Math]::Floor([Windows.SystemParameters]::WorkArea.Width))
    if ($settings.Theme -ne 'AMOLED-HighContrast-FullScreen' -or $settings.ColorScheme -ne 'Dark' -or
        $settings.SearchWindowAlign -ne 'Custom' -or $settings.CustomWindowLeft -ne 0 -or
        $settings.CustomWindowTop -ne 0 -or $settings.WindowSize -ne $expectedWidth -or
        $settings.KeepThis -ne 'unchanged' -or -not $runtime.runtimeOptions.configProperties.ExistingOption -or
        $runtime.runtimeOptions.configProperties.'Switch.System.Windows.Controls.Text.UseAdornerForTextboxSelectionRendering' -ne $false) {
        throw 'The full-screen configuration fixture failed validation.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $fixtureFull 'UserData\Themes\AMOLED-HighContrast-FullScreen.xaml'))) {
        throw 'The theme was not installed in the fixture.'
    }
    Write-Output 'Flow Launcher configuration fixture passed.'
} finally {
    if (Test-Path -LiteralPath $fixtureFull) { Remove-Item -LiteralPath $fixtureFull -Recurse -Force }
}
