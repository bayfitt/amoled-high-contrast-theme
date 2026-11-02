#!/usr/bin/env python3
"""Generate app-specific themes from the shared palette."""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "palette.json").read_text(encoding="utf-8"))


def replace_tokens(template, values):
    def sub(match):
        name = match.group(1)
        if name not in values:
            raise ValueError(f"Unknown theme token: {name}")
        return str(values[name])
    return re.sub(r"\{\{([a-z_]+)\}\}", sub, template)


def flow_theme(full_height):
    values = dict(PALETTE)
    values["background_argb"] = "#FF" + values["background"][1:]
    values["flow_name"] = "AMOLED High Contrast Full Screen" if full_height else "AMOLED High Contrast"
    values["flow_corner_radius"] = "0" if full_height else "8"
    values["flow_converter"] = (
        '    <converters:SizeRatioConverter x:Key="WorkAreaHeightRatio" />\n'
        if full_height else ""
    )
    values["flow_height_setter"] = (
        '        <Setter Property="MinHeight">\n'
        '            <Setter.Value>\n'
        '                <Binding Path="Height" Source="{x:Static SystemParameters.WorkArea}"\n'
        '                         Converter="{StaticResource WorkAreaHeightRatio}" ConverterParameter="1" />\n'
        '            </Setter.Value>\n'
        '        </Setter>\n'
        if full_height else ""
    )
    template = (ROOT / "templates" / "flow-launcher.xaml.in").read_text(encoding="utf-8")
    return replace_tokens(template, values)


def codex_monitor_theme():
    text = (ROOT / "templates" / "codex-monitor-amoled-original.css").read_text(encoding="utf-8")
    cyan = PALETTE["text_primary"]
    selection = PALETTE["selection_background"]
    selection_text = PALETTE["selection_text"]
    text = re.sub(r"(?m)^(\s*--text-[\w-]+:\s*)[^;]+;", lambda m: m.group(1) + cyan + ";", text)
    text = re.sub(r"(?m)^(\s*--message-link-color:\s*)[^;]+;", lambda m: m.group(1) + cyan + ";", text)
    text = re.sub(r"(?m)^(\s*--surface-active:\s*)[^;]+;", lambda m: m.group(1) + selection + ";", text)
    text = re.sub(r"(?m)^(\s*(?:color|caret-color):\s*)[^;]+;", lambda m: m.group(1) + cyan + ";", text)
    # Shift the former magenta/violet surfaces to the same royal-purple family.
    text = re.sub(r"hsl\((?:2[89]\d|3[01]\d)(?=\s)", "hsl(260", text, flags=re.IGNORECASE)
    pattern = r'(:root\[data-theme="amoled"\] ::selection\s*\{)(.*?)(\})'
    text, count = re.subn(pattern, lambda m: m.group(1) + f"\n  background: {selection};\n  color: {selection_text};\n" + m.group(3), text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("The Codex Monitor selection rule could not be found")
    text += f'''
/* Keep ordinary and selected text white.
   Image and emoji icons retain their original colors. */
:root[data-theme="amoled"] :where(div, p, span, a, button, label, input, textarea, select, option, h1, h2, h3, h4, h5, h6, code, pre, li, td, th, small, strong, em, kbd, time, summary, blockquote) {{
  color: {cyan} !important;
}}
:root[data-theme="amoled"] ::selection {{
  background: {selection} !important;
  color: {selection_text} !important;
}}
:root[data-theme="amoled"] :is(.is-selected, [aria-selected="true"]),
:root[data-theme="amoled"] :is(.is-selected, [aria-selected="true"]) :where(div, p, span, a, button, label, code, pre) {{
  color: {selection_text} !important;
}}
:root[data-theme="amoled"] :is(.is-selected, [aria-selected="true"]) {{
  outline: 2px solid {PALETTE["accent_cyan"]};
  outline-offset: -2px;
}}
'''
    return text


def generic_css():
    p = PALETTE
    return f'''/* AMOLED High Contrast: import this file and add data-theme="amoled-high-contrast" to the root. */
[data-theme="amoled-high-contrast"] {{
  color-scheme: dark;
  --amoled-background: {p["background"]};
  --amoled-text: {p["text_primary"]};
  --amoled-selection: {p["selection_background"]};
  --amoled-selection-text: {p["selection_text"]};
  --amoled-accent-cyan: {p["accent_cyan"]};
  --amoled-accent-purple: {p["accent_purple"]};
  background-color: var(--amoled-background);
  color: var(--amoled-text);
}}
[data-theme="amoled-high-contrast"] ::selection {{
  background: var(--amoled-selection);
  color: var(--amoled-selection-text);
}}
[data-theme="amoled-high-contrast"] :is(.is-selected, [aria-selected="true"]) {{
  background-color: var(--amoled-selection);
  color: var(--amoled-selection-text);
  outline: 2px solid var(--amoled-accent-cyan);
  outline-offset: -2px;
}}
'''


def generated():
    return {
        "adapters/flow-launcher/AMOLED-HighContrast.xaml": flow_theme(False),
        "adapters/flow-launcher/AMOLED-HighContrast-FullScreen.xaml": flow_theme(True),
        "adapters/codex-monitor/themes.amoled.css": codex_monitor_theme(),
        "adapters/css/amoled-high-contrast.css": generic_css(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check that generated files match the palette")
    args = parser.parse_args()
    bad = []
    for name, content in generated().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                bad.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
            print(name)
    if bad:
        print("Out-of-date generated files: " + ", ".join(bad), file=sys.stderr)
        return 1
    if args.check:
        print("Generated theme files match palette.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
