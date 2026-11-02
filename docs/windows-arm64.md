# Windows on ARM64

The palette, CSS, and XAML are architecture-independent. They can be used by compatible Windows x64 or ARM64 builds of the relevant applications; the theme itself is not an executable and does not determine the process architecture.

For Flow Launcher, choose an ARM64 build if a native process is required. The public Flow Launcher ARM64 implementation at [pull request 4659](https://github.com/Flow-Launcher/Flow.Launcher/pull/4659) was still under review when this adapter was created. Follow that pull request's build instructions and apply the Flow theme from this repository to the resulting compatible build.

For Codex Monitor, use the Windows ARM64 build configuration in the source checkout being built. Replace `src/styles/themes.amoled.css` with this repository's adapter before building, and keep a backup of any local changes. The result should be verified on the target device; the theme file alone is not proof that the application is running natively.
