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
    # Quiet text and placeholders use the requested red; status and syntax
    # colors retain their existing semantic roles.
    text = re.sub(
        r"(?m)^(\s*--text-(?:quiet|muted|subtle|faint|fainter|dim):\s*)[^;]+;",
        lambda m: m.group(1) + PALETTE["text_secondary"] + ";",
        text,
    )
    text = re.sub(r"(?m)^(\s*--message-link-color:\s*)[^;]+;", lambda m: m.group(1) + cyan + ";", text)
    text = re.sub(r"(?m)^(\s*--surface-active:\s*)[^;]+;", lambda m: m.group(1) + selection + ";", text)
    text = re.sub(r"(?m)^(\s*(?:color|caret-color):\s*)[^;]+;", lambda m: m.group(1) + cyan + ";", text)
    # Keep blue and purple backgrounds close to black. Preserve colorful
    # text/status semantics rather than turning dark colors into foregrounds.
    def dark_surfaces(match):
        def darken(color):
            hue = int(color.group(1)) % 360
            if 200 <= hue < 270:
                return PALETTE["hover_background"]
            if 270 <= hue < 330:
                return PALETTE["selection_background"]
            return color.group(0)
        value = re.sub(r"hsl\((\d+)\s+[^)]*\)", darken, match.group(2), flags=re.IGNORECASE)
        return match.group(1) + value + ";"
    text = re.sub(
        r"(?m)^(\s*(?:--surface-[\w-]+|background(?:-image)?):\s*)([^;]+);",
        dark_surfaces,
        text,
    )
    # Recolor the stylesheet's own visible borders, without changing
    # transparent borders or pseudo-elements used for icons and shapes.
    text = re.sub(
        r"(?m)^(\s*--border-[\w-]+:\s*)[^;]+;",
        lambda m: m.group(1) + PALETTE["accent_orange"] + ";",
        text,
    )
    text = re.sub(
        r"\bborder-color:\s*hsl\([^)]*\);",
        lambda m: f'border-color: {PALETTE["accent_orange"]}; border-width: 1px;',
        text,
        flags=re.IGNORECASE,
    )
    # Retain a readable unread marker without a bright-blue indicator.
    text = text.replace(
        '.thread-status.unread { background: hsl(220 100% 60%); }',
        f'.thread-status.unread {{ background: {PALETTE["accent_yellow"]}; }}',
    )
    text = text.replace(
        'color: hsl(220 100% 80%); background: hsl(220 100% 12%);',
        f'color: {PALETTE["accent_yellow"]}; background: {PALETTE["hover_background"]};',
    )
    text = text.replace(
        'box-shadow: inset 0 1px 0 hsl(210 100% 22%);',
        f'box-shadow: inset 0 1px 0 {PALETTE["accent_orange"]};',
    )
    text = text.replace(
        f'.thread-row:hover {{\n  background: {PALETTE["selection_background"]};',
        f'.thread-row:hover {{\n  background: {PALETTE["hover_background"]};',
    )
    text = re.sub(
        r'(?m)^(\s*--shadow-accent:\s*)[^;]+;',
        lambda m: m.group(1) + PALETTE["selection_background"] + ';',
        text,
    )
    pattern = r'(:root\[data-theme="amoled"\] ::selection\s*\{)(.*?)(\})'
    text, count = re.subn(pattern, lambda m: m.group(1) + f"\n  background: {selection};\n  color: {selection_text};\n" + m.group(3), text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("The Codex Monitor selection rule could not be found")
    text += f'''
/* Keep primary and selected text white, and quiet text light red.
   Image and emoji icons retain their original colors. */
:root[data-theme="amoled"] :where(div, p, span, a, button, label, input, textarea, select, option, h1, h2, h3, h4, h5, h6, code, pre, li, td, th, small, strong, em, kbd, time, summary, blockquote) {{
  color: {cyan} !important;
}}
:root[data-theme="amoled"] :is(.home-usage-label, .workspace-summary, .thread-time, .sidebar-usage-reset),
:root[data-theme="amoled"] :is(.home-usage-label, .workspace-summary, .thread-time, .sidebar-usage-reset) :where(span, small, time),
:root[data-theme="amoled"] :is(input, textarea)::placeholder {{
  color: {PALETTE["text_secondary"]} !important;
  opacity: 1;
}}
:root[data-theme="amoled"] .thread-state-chip.unread,
:root[data-theme="amoled"] .thread-state-chip.unread :where(span, small) {{
  color: {PALETTE["accent_yellow"]} !important;
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
  outline: 1px solid {PALETTE["accent_orange"]};
  outline-offset: -1px;
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
  --amoled-text-secondary: {p["text_secondary"]};
  --amoled-selection: {p["selection_background"]};
  --amoled-selection-text: {p["selection_text"]};
  --amoled-accent-red: {p["text_secondary"]};
  --amoled-accent-orange: {p["accent_orange"]};
  --amoled-accent-yellow: {p["accent_yellow"]};
  --amoled-accent-green: {p["accent_green"]};
  --amoled-accent-cyan: {p["accent_cyan"]};
  --amoled-accent-blue: {p["hover_background"]};
  --amoled-accent-purple: {p["accent_purple"]};
  background-color: var(--amoled-background);
  color: var(--amoled-text);
}}
[data-theme="amoled-high-contrast"] ::selection {{
  background: var(--amoled-selection);
  color: var(--amoled-selection-text);
}}
[data-theme="amoled-high-contrast"] :is(.amoled-secondary, [data-amoled-secondary]) {{
  color: var(--amoled-text-secondary);
}}
[data-theme="amoled-high-contrast"] :is(.is-selected, [aria-selected="true"]) {{
  background-color: var(--amoled-selection);
  color: var(--amoled-selection-text);
  outline: 1px solid var(--amoled-accent-orange);
  outline-offset: -1px;
}}
'''


def zapfast_theme():
    """Map the shared spectrum to ZapFast's supported palette roles."""
    p = PALETTE
    colors = {
        "window": p["background"],
        "panel": p["background"],
        "surface": "#101010",
        "surface_hover": p["hover_background"],
        "surface_active": p["selection_background"],
        "outline": p["accent_orange"],
        "text": p["text_primary"],
        "secondary": p["text_secondary"],
        "dim": p["text_secondary"],
        "accent": p["control_orange"],
        "accent_hover": p["control_orange_hover"],
        "on_accent": p["selection_text"],
        "danger": "#FF7070",
        "warning": p["accent_yellow"],
        "overlay": p["background"],
        "shadow": p["background"],
        "chat": p["background"],
        "bubble_in": "#101010",
        "bubble_out": p["selection_background"],
        "link": p["accent_cyan"],
        "read": p["accent_green"],
    }
    return json.dumps({"base": "dark", "colors": colors}, indent=2) + "\n"


def generated():
    return {
        "adapters/flow-launcher/AMOLED-HighContrast.xaml": flow_theme(False),
        "adapters/flow-launcher/AMOLED-HighContrast-FullScreen.xaml": flow_theme(True),
        "adapters/codex-monitor/themes.amoled.css": codex_monitor_theme(),
        "adapters/css/amoled-high-contrast.css": generic_css(),
        "adapters/zapfast/AMOLED High Contrast.json": zapfast_theme(),
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
