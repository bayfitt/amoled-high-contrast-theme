#!/usr/bin/env python3
"""Check the shared palette's contrast and generated adapters."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "palette.json").read_text(encoding="utf-8"))


def luminance(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class ThemeTests(unittest.TestCase):
    def test_text_and_selection_contrast(self):
        self.assertGreaterEqual(contrast(PALETTE["text_primary"], PALETTE["background"]), 7)
        self.assertGreaterEqual(contrast(PALETTE["selection_text"], PALETTE["selection_background"]), 4.5)
        self.assertEqual(PALETTE["selection_text"], PALETTE["text_primary"])
        self.assertGreaterEqual(contrast(PALETTE["accent_orange"], PALETTE["selection_background"]), 3)
        self.assertGreaterEqual(contrast(PALETTE["accent_orange"], PALETTE["background"]), 3)
        for background in (PALETTE["selection_background"], PALETTE["hover_background"]):
            self.assertLess(luminance(background), 0.02)
            self.assertIn("00", (background[1:3], background[3:5], background[5:7]))
            self.assertGreaterEqual(contrast(PALETTE["accent_orange"], background), 3)

    def test_selected_outlines_and_known_css_borders(self):
        for path in (ROOT / "adapters" / "css" / "amoled-high-contrast.css",
                     ROOT / "adapters" / "codex-monitor" / "themes.amoled.css"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("outline: 1px solid", text)
            self.assertNotIn(":where(*)::before", text)
            self.assertNotIn("border-width: 1px !important;", text)
        css = (ROOT / "adapters" / "codex-monitor" / "themes.amoled.css").read_text(encoding="utf-8")
        self.assertIn(f'border-color: {PALETTE["accent_orange"]}; border-width: 1px;', css)
        self.assertIn(f'--border-muted: {PALETTE["accent_orange"]};', css)
        self.assertIn(f'.thread-state-chip.unread {{ color: {PALETTE["accent_yellow"]}; background: {PALETTE["hover_background"]};', css)
        self.assertIn(f'.thread-row:hover {{\n  background: {PALETTE["hover_background"]};', css)
        self.assertNotIn('hsl(220 100% 80%)', css)

    def test_flow_themes_are_xml_with_white_selection_text(self):
        for path in (ROOT / "adapters" / "flow-launcher").glob("*.xaml"):
            text = path.read_text(encoding="utf-8")
            ET.fromstring(text)
            self.assertIn(f'Property="SelectionTextBrush" Value="{PALETTE["selection_text"]}"', text)
            self.assertIn(f'Property="SelectionBrush" Value="{PALETTE["selection_background"]}"', text)
            self.assertIn(f'Property="BorderBrush" Value="{PALETTE["accent_orange"]}"', text)
            self.assertIn('Property="BorderThickness" Value="1"', text)
            indicator = re.search(r'x:Key="ItemBulletSelectedStyle".*?</Style>', text, re.DOTALL).group()
            self.assertIn('Property="Width" Value="1"', indicator)
            self.assertIn(f'Property="Background" Value="{PALETTE["accent_orange"]}"', indicator)
            self.assertNotIn("{{", text)

    def test_full_screen_has_no_intentional_margin(self):
        path = ROOT / "adapters" / "flow-launcher" / "AMOLED-HighContrast-FullScreen.xaml"
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        wpf = "{http://schemas.microsoft.com/winfx/2006/xaml/presentation}"
        key = "{http://schemas.microsoft.com/winfx/2006/xaml}Key"
        style = next(element for element in root.findall(wpf + "Style") if element.get(key) == "WindowBorderStyle")
        self.assertTrue(any(s.get("Property") == "CornerRadius" and s.get("Value") == "0" for s in style))
        binding = style.find(".//" + wpf + "Binding")
        self.assertIsNotNone(binding)
        self.assertEqual(binding.get("ConverterParameter"), "1")

    def test_codex_selection_and_text(self):
        css = (ROOT / "adapters" / "codex-monitor" / "themes.amoled.css").read_text(encoding="utf-8")
        self.assertIn(f'background: {PALETTE["selection_background"]} !important;', css)
        self.assertIn(f'color: {PALETTE["selection_text"]} !important;', css)
        quiet = {"quiet", "muted", "subtle", "faint", "fainter", "dim"}
        for name, value in re.findall(r"(?m)^\s*--text-([\w-]+):\s*([^;]+);", css):
            self.assertEqual(value, PALETTE["text_secondary"] if name in quiet else PALETTE["text_primary"])
        self.assertIn(f'color: {PALETTE["text_secondary"]} !important;', css)

    def test_flow_secondary_text_uses_warm_white(self):
        for path in (ROOT / "adapters" / "flow-launcher").glob("*.xaml"):
            text = path.read_text(encoding="utf-8")
            sub_style = re.search(r'x:Key="ItemSubTitleStyle".*?</Style>', text, re.DOTALL).group()
            self.assertIn(f'Property="Foreground" Value="{PALETTE["text_secondary"]}"', sub_style)
            selected = re.search(r'x:Key="ItemSubTitleSelectedStyle".*?</Style>', text, re.DOTALL).group()
            self.assertIn(f'Property="Foreground" Value="{PALETTE["selection_text"]}"', selected)

    def test_zapfast_semantic_contrasts(self):
        theme = json.loads((ROOT / "adapters" / "zapfast" / "AMOLED High Contrast.json").read_text(encoding="utf-8"))
        colors = theme["colors"]
        self.assertEqual(theme["base"], "dark")
        self.assertEqual(colors["surface_active"], PALETTE["selection_background"])
        # ZapFast derives selected glyphs and the translucent highlight from
        # the same accent. White on a 35% white overlay over black is readable.
        self.assertEqual(colors["accent"], "#FFFFFF")
        self.assertGreaterEqual(contrast(colors["accent"], "#595959"), 4.5)
        for background in (colors["window"], colors["surface"], colors["surface_active"], colors["surface_hover"]):
            for foreground in (colors["text"], colors["secondary"], colors["dim"]):
                self.assertGreaterEqual(contrast(foreground, background), 4.5, (foreground, background))
            self.assertGreaterEqual(contrast(colors["outline"], background), 3, (colors["outline"], background))
        for background in (colors["accent"], colors["accent_hover"]):
            self.assertGreaterEqual(contrast(colors["on_accent"], background), 4.5)
        for foreground in (colors["warning"], colors["read"], colors["link"]):
            for background in (colors["window"], colors["surface_active"], colors["surface_hover"]):
                self.assertGreaterEqual(contrast(foreground, background), 3)

    def test_generated_files_match_palette(self):
        subprocess.run([sys.executable, str(ROOT / "tools" / "generate.py"), "--check"], check=True)


if __name__ == "__main__":
    unittest.main()
