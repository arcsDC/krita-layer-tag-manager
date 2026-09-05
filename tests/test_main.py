import unittest
import sys
import os
import json
import tempfile
from unittest.mock import MagicMock, patch

# Mock krita module before importing the main module
mock_krita = MagicMock()
sys.modules['krita'] = mock_krita

# Import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import krita_layer_tag_manager as kltm

class TestTagManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.preset_path = os.path.join(self.temp_dir, "layer_tags.json")
        # Patch the path used in TagManager
        self.patcher = patch('krita_layer_tag_manager.os.path.expanduser', return_value=self.temp_dir)
        self.patcher.start()
        self.tag_manager = kltm.TagManager()

    def tearDown(self):
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_get_tag(self):
        self.tag_manager.add_tag("test_tag", "#FF0000")
        self.assertEqual(self.tag_manager.get_tag_color("test_tag"), "#FF0000")
        self.assertIn("test_tag", self.tag_manager.tags)

    def test_remove_tag(self):
        self.tag_manager.add_tag("temp_tag", "#00FF00")
        self.tag_manager.remove_tag("temp_tag")
        self.assertNotIn("temp_tag", self.tag_manager.tags)

    def test_persistence(self):
        self.tag_manager.add_tag("persisted", "#0000FF")
        # Create a new instance to test loading
        new_manager = kltm.TagManager()
        self.assertEqual(new_manager.get_tag_color("persisted"), "#0000FF")

    def test_invalid_preset_file(self):
        # Write invalid JSON to preset path
        with open(self.preset_path, 'w') as f:
            f.write("invalid json")
        manager = kltm.TagManager()
        self.assertEqual(manager.tags, {})

class TestLayerTagWidget(unittest.TestCase):
    def setUp(self):
        self.tag_manager = kltm.TagManager()
        self.widget = kltm.LayerTagWidget(self.tag_manager)

    def test_add_tag_via_ui(self):
        self.widget.tag_input.setText("ui_tag")
        self.widget.add_tag()
        self.assertIn("ui_tag", self.tag_manager.tags)
        self.assertEqual(self.widget.tag_input.text(), "")

    def test_add_empty_tag(self):
        self.widget.tag_input.setText("   ")
        self.widget.add_tag()
        self.assertEqual(len(self.tag_manager.tags), 0)

if __name__ == '__main__':
    unittest.main()
