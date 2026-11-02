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
        self.assertGreaterEqual(contrast(PALETTE["accent_cyan"], PALETTE["selection_background"]), 3)
        self.assertGreaterEqual(contrast(PALETTE["accent_cyan"], PALETTE["background"]), 3)

    def test_flow_themes_are_xml_with_cyan_selection_text(self):
        for path in (ROOT / "adapters" / "flow-launcher").glob("*.xaml"):
            text = path.read_text(encoding="utf-8")
            ET.fromstring(text)
            self.assertIn(f'Property="SelectionTextBrush" Value="{PALETTE["selection_text"]}"', text)
            self.assertIn(f'Property="SelectionBrush" Value="{PALETTE["selection_background"]}"', text)
            self.assertNotIn("{{", text)

    def test_codex_selection_and_text(self):
        css = (ROOT / "adapters" / "codex-monitor" / "themes.amoled.css").read_text(encoding="utf-8")
        self.assertIn(f'background: {PALETTE["selection_background"]} !important;', css)
        self.assertIn(f'color: {PALETTE["selection_text"]} !important;', css)
        for value in re.findall(r"(?m)^\s*--text-[\w-]+:\s*([^;]+);", css):
            self.assertEqual(value, PALETTE["text_primary"])

    def test_generated_files_match_palette(self):
        subprocess.run([sys.executable, str(ROOT / "tools" / "generate.py"), "--check"], check=True)


if __name__ == "__main__":
    unittest.main()
