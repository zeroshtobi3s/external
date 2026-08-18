import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ext.offsets import OFFSET_FILES, Client


class OffsetClientTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temporary_directory.name) / ".cache"
        self.offsets = {"client.dll": {"dwEntityList": 123}}
        self.client_dll = {"client.dll": {"classes": {}}}
        self.buttons = {"client.dll": {"jump": 456}}

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _client_with_data(self):
        client = object.__new__(Client)
        client.cache_dir = self.cache_dir
        client.offsets = self.offsets
        client.clientdll = self.client_dll
        client.buttons = self.buttons
        return client

    def test_write_cache_and_load_from_explicit_directory(self):
        writer = self._client_with_data()
        writer._write_cache()

        self.assertEqual(set(OFFSET_FILES), {path.name for path in self.cache_dir.iterdir()})
        self.assertEqual(self.offsets, json.loads((self.cache_dir / "offsets.json").read_text()))

        reader = object.__new__(Client)
        reader.cache_dir = self.cache_dir
        reader._load_from_file(self.cache_dir)

        self.assertEqual(self.offsets, reader.offsets)
        self.assertEqual(self.client_dll, reader.clientdll)
        self.assertEqual(self.buttons, reader.buttons)

    def test_http_json_requires_a_successful_response(self):
        response = Mock()
        response.json.return_value = self.offsets
        with patch("ext.offsets.requests.get", return_value=response) as get:
            result = Client._get_json_from_url("https://example.invalid/offsets.json")

        self.assertEqual(self.offsets, result)
        get.assert_called_once_with("https://example.invalid/offsets.json", timeout=5)
        response.raise_for_status.assert_called_once()

    def test_load_from_url_falls_back_to_existing_cache(self):
        writer = self._client_with_data()
        writer._write_cache()

        client = object.__new__(Client)
        client.cache_dir = self.cache_dir
        with patch.object(Client, "_get_json_from_url", side_effect=OSError("offline")):
            client._load_from_url()

        self.assertEqual(self.offsets, client.offsets)
        self.assertEqual(self.client_dll, client.clientdll)
        self.assertEqual(self.buttons, client.buttons)


if __name__ == "__main__":
    unittest.main()
