# AMOLED High Contrast

A reusable high-contrast theme with a pure-black background, white text, and a dark royal-purple selection. White text stays white when selected. Colorful image and emoji icons can keep their colors.

This repository is the source of truth for the palette. It provides adapters for specific applications; applications must support custom themes or include an adapter in their build. A Windows theme cannot force every application to use the same colors.

## Palette

| Use | Color | Contrast |
| --- | --- | --- |
| Background | `#000000` | — |
| Text and selected text | `#FFFFFF` | 21:1 against black; 9.17:1 against the selection |
| Selection background | `#512DA8` | Dark royal purple |
| Selection indicator | `#00EAFF` | Bright cyan against both the black and purple surfaces |

The palette is in [palette.json](palette.json). Cyan and light purple accents are used for borders, icons, or other decoration. A bright indicator distinguishes a selected row from the black background. The contrast values above use the WCAG relative-luminance formula.

Open [preview.html](preview.html) locally to try the colors and select some text.

## Flow Launcher

- [AMOLED High Contrast](adapters/flow-launcher/AMOLED-HighContrast.xaml) keeps the normal window sizing.
- [AMOLED High Contrast Full Screen](adapters/flow-launcher/AMOLED-HighContrast-FullScreen.xaml) makes the window as tall as the primary monitor's usable work area. Set the window width and position to fill that area edge to edge.

For a portable build, close Flow Launcher and run the PowerShell 7 helper with the folder containing `Flow.Launcher.exe`:

```powershell
./tools/configure-flow-launcher.ps1 -FlowRoot 'C:\Path\To\FlowLauncher' -Layout FullScreen
```

The helper backs up the existing settings and runtime configuration, installs the theme, and configures the window for the primary work area. Use `-Layout Normal` for the normal-width theme. It also enables WPF's non-adorner text-selection rendering so white letters remain visible on an opaque highlight. Restart Flow Launcher afterward.

Alternatively, copy the XAML to Flow's user theme directory: `%APPDATA%\FlowLauncher\Themes` for a standard installation, or `UserData\Themes` beside the executable for a portable build. Merge the setting from [runtimeconfig.template.json](adapters/flow-launcher/runtimeconfig.template.json) into that build's `Flow.Launcher.runtimeconfig.json`, preserving its other settings. In **Settings → Appearance**, choose the theme and **Dark** color scheme. For full screen, use a custom top-left position of `(0, 0)`, turn off the drop shadow, and set the width to fit the display.

The full-screen variant reads the primary Windows work-area height when the theme loads, and the helper sets the width from that work area. It does not dynamically measure a different monitor; rerun the helper after display scaling or monitor configuration changes. The theme file is architecture-independent and works with compatible x64 and native ARM64 builds.

## Codex Monitor

[themes.amoled.css](adapters/codex-monitor/themes.amoled.css) adapts the user's existing AMOLED design: black surfaces and colorful accents remain, while normal and selected text are white and selections use royal purple.

To use it in a Codex Monitor source build, back up the existing `src/styles/themes.amoled.css`, replace it with the adapter, and build the application using that checkout's normal instructions. Select **AMOLED** in Codex Monitor's appearance settings. The CSS is embedded in a compiled application, so replacing this repository file alone will not change an already installed build. See [Windows on ARM64](docs/windows-arm64.md) for architecture notes.

## Other applications and web views

[amoled-high-contrast.css](adapters/css/amoled-high-contrast.css) exposes the shared colors as CSS variables. Import it and set `data-theme="amoled-high-contrast"` on a parent element, then use the variables in the application's styles. New applications can consume [palette.json](palette.json) and implement the same semantic roles in their own theme format.

## Update the palette

1. Edit [palette.json](palette.json).
2. Run `python tools/generate.py` to regenerate every adapter.
3. Run `python tools/test_theme.py` and `python tools/generate.py --check`.
4. Reapply or rebuild the adapters used by each application.

The automated checks cover text/selection contrast, generated-file consistency, and XML syntax. They do not replace a visual check in each application.

## Licenses and attribution

The repository's original work is MIT licensed; see [LICENSE](LICENSE). The Flow Launcher theme is adapted from Flow Launcher's `Midnight.xaml`, and the Codex Monitor adapter is based on its AMOLED stylesheet. Their original MIT license notices are included in [licenses](licenses).
