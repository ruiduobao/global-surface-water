#!/usr/bin/env python3
"""
Tests for global-surface-water CLI.
Run with: python -m pytest tests/ -v
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    import global_surface_water as gsw
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "global_surface_water",
        str(Path(__file__).parent.parent / "scripts" / "global_surface_water.py"),
    )
    gsw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gsw)


class TestValidation(unittest.TestCase):
    """Test input validation functions."""

    def test_validate_bbox_valid(self):
        """Test valid bounding box."""
        result = gsw.validate_bbox([73, 18, 135, 54])
        self.assertEqual(result, (73, 18, 135, 54))

    def test_validate_bbox_invalid_order(self):
        """Test invalid bbox (south >= north)."""
        with self.assertRaises(ValueError):
            gsw.validate_bbox([73, 54, 135, 18])

    def test_validate_bbox_invalid_lat(self):
        """Test invalid latitude in bbox."""
        with self.assertRaises(ValueError):
            gsw.validate_bbox([73, 91, 135, 54])

    def test_validate_layer_valid(self):
        """Test valid layer names."""
        self.assertEqual(gsw.validate_layer("occurrence"), "occurrence")
        self.assertEqual(gsw.validate_layer("OCCURRENCE"), "occurrence")
        self.assertEqual(gsw.validate_layer("all"), "all")
        self.assertEqual(gsw.validate_layer("ALL"), "all")

    def test_validate_layer_invalid(self):
        """Test invalid layer name."""
        with self.assertRaises(ValueError):
            gsw.validate_layer("invalid_layer")


class TestTileCalculation(unittest.TestCase):
    """Test tile calculation functions."""

    def test_get_tile_range_single(self):
        """Test tile calculation for small bbox (single tile)."""
        bbox = (116.0, 39.5, 116.8, 40.2)
        tiles = gsw.get_tile_range(bbox)
        self.assertGreater(len(tiles), 0)
        # All tiles should be within the expected range
        # Tile lower-left corners: lon should be <= west, lat should be <= north's tile floor
        for lon, lat in tiles:
            self.assertLessEqual(lon, 116.0)
            self.assertLessEqual(lat, 40.0)

    def test_get_tile_range_multiple(self):
        """Test tile calculation for larger bbox (multiple tiles)."""
        bbox = (73, 18, 135, 54)
        tiles = gsw.get_tile_range(bbox)
        self.assertGreater(len(tiles), 1)
        # Should cover multiple tiles
        self.assertGreater(len(tiles), 10)

    def test_get_download_url(self):
        """Test download URL generation."""
        url = gsw.get_download_url("occurrence", 110, 30)
        self.assertIn("occurrence", url)
        self.assertIn("tif", url)
        self.assertTrue(url.startswith("https://"))

    def test_get_download_url_negative_coords(self):
        """Test download URL for negative coordinates."""
        url = gsw.get_download_url("occurrence", -10, -20)
        self.assertIn("occurrence", url)
        self.assertTrue(url.startswith("https://"))


class TestLayers(unittest.TestCase):
    """Test layer definitions."""

    def test_all_layers_have_required_fields(self):
        """Test that all layers have required metadata."""
        required_fields = ["label", "description", "unit"]
        for layer_name, layer_info in gsw.LAYERS.items():
            for field in required_fields:
                self.assertIn(field, layer_info,
                              f"Layer {layer_name} missing field: {field}")

    def test_layers_count(self):
        """Test that we have 7 layers defined."""
        self.assertEqual(len(gsw.LAYERS), 7)


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_help_message(self):
        """Test that help message can be displayed."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["global-surface-water", "--help"]):
                gsw.main()
        self.assertEqual(cm.exception.code, 0)

    def test_list_layers_command(self):
        """Test list-layers command."""
        with patch("sys.argv", ["global-surface-water", "list-layers"]):
            gsw.main()

    def test_info_command(self):
        """Test info command."""
        with patch("sys.argv", ["global-surface-water", "info"]):
            gsw.main()

    def test_download_help(self):
        """Test download subcommand help."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["global-surface-water", "download", "--help"]):
                gsw.main()
        self.assertEqual(cm.exception.code, 0)


class TestDownloadURLGeneration(unittest.TestCase):
    """Test download URL generation for various scenarios."""

    def test_url_format_occurrence(self):
        """Test URL format for occurrence layer."""
        url = gsw.get_download_url("occurrence", 110, 30, "v1_4")
        self.assertIn("occurrence_v1_4", url)
        self.assertTrue(url.endswith(".tif"))

    def test_url_format_change(self):
        """Test URL format for change layer."""
        url = gsw.get_download_url("change", 0, 0, "v1_4")
        self.assertIn("change_v1_4", url)


if __name__ == "__main__":
    unittest.main()
