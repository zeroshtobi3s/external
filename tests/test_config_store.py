import json
import tempfile
import unittest
from pathlib import Path

from functions.config_store import load_settings, save_settings


class ConfigStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temporary_directory.name) / "config" / "settings.json"
        self.defaults = {
            "enabled": False,
            "fov": 90,
            "new_setting": True,
        }

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_file_creates_default_settings(self):
        loaded = load_settings(self.defaults, self.settings_path)

        self.assertEqual(self.defaults, loaded)
        self.assertTrue(self.settings_path.exists())
        self.assertEqual(self.defaults, json.loads(self.settings_path.read_text(encoding="utf-8")))

    def test_legacy_settings_keep_new_defaults_and_existing_values(self):
        self.settings_path.parent.mkdir(parents=True)
        self.settings_path.write_text(
            json.dumps({"enabled": True, "fov": 110, "legacy_setting": "keep"}),
            encoding="utf-8",
        )

        loaded = load_settings(self.defaults, self.settings_path)

        self.assertTrue(loaded["enabled"])
        self.assertEqual(110, loaded["fov"])
        self.assertTrue(loaded["new_setting"])
        self.assertEqual("keep", loaded["legacy_setting"])

    def test_invalid_json_returns_defaults_without_replacing_user_file(self):
        self.settings_path.parent.mkdir(parents=True)
        self.settings_path.write_text("{invalid json", encoding="utf-8")

        loaded = load_settings(self.defaults, self.settings_path)

        self.assertEqual(self.defaults, loaded)
        self.assertEqual("{invalid json", self.settings_path.read_text(encoding="utf-8"))

    def test_save_is_readable_and_leaves_no_temporary_files(self):
        settings = {"enabled": True, "fov": 100}

        self.assertTrue(save_settings(settings, self.settings_path))

        self.assertEqual(settings, json.loads(self.settings_path.read_text(encoding="utf-8")))
        self.assertEqual([], list(self.settings_path.parent.glob(".settings.json.*.tmp")))


if __name__ == "__main__":
    unittest.main()
