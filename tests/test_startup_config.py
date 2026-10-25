"""Check fresh-deployment configuration and safe startup file handling."""

import ast
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
VALID_ENV = {
    "API_ID": "12345", "API_HASH": "test-api-hash", "BOT_TOKEN": "12345:test-token",
    "LOGGER_ID": "-100123456", "MONGO_DB_URI": "mongodb://localhost:27017",
}


def read_config(values):
    with patch.dict(os.environ, values, clear=True), patch("dotenv.load_dotenv"):
        config = runpy.run_path(str(ROOT / "config.py"))
        config["validate_config"]()
        return config


class StartupConfigTest(unittest.TestCase):
    def test_missing_credentials_fail_before_any_clients_are_started(self):
        with self.assertRaises(SystemExit) as error:
            read_config({})
        for name in VALID_ENV:
            self.assertIn(name, str(error.exception))

    def test_empty_required_values_give_actionable_error(self):
        values = {**VALID_ENV, "API_ID": "", "API_HASH": "", "LOGGER_ID": ""}
        with self.assertRaises(SystemExit) as error:
            read_config(values)
        self.assertIn("API_ID", str(error.exception))
        self.assertIn("LOGGER_ID", str(error.exception))

    def test_invalid_owner_is_reported_without_echoing_input(self):
        with self.assertRaises(SystemExit) as error:
            read_config({**VALID_ENV, "OWNER_ID": "private-invalid-input"})
        self.assertIn("OWNER_ID must be an integer", str(error.exception))
        self.assertNotIn("private-invalid-input", str(error.exception))

    def test_fresh_deployment_and_blank_owner_use_requested_presets(self):
        for extra in ({}, {"OWNER_ID": ""}):
            config = read_config({**VALID_ENV, **extra})
            self.assertEqual(config["OWNER_ID"], 73265606)
            self.assertEqual(config["OWNER_USERNAME"], "iflexelite")
            self.assertEqual(config["BOT_USERNAME"], "The_RaHa_BoT")
            self.assertEqual(config["BOT_NAME"], "Aetherion Music")

    def test_deployment_can_override_owner(self):
        self.assertEqual(read_config({**VALID_ENV, "OWNER_ID": "42"})["OWNER_ID"], 42)


class DirectoryStartupTest(unittest.TestCase):
    def test_startup_keeps_user_images_and_only_cleans_partial_downloads(self):
        tree = ast.parse((ROOT / "AETH/core/dir.py").read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            logo = base / "logo.png"
            logo.write_bytes(b"user image")
            downloads = base / "downloads"
            downloads.mkdir()
            partial = downloads / "song.downloading"
            partial.write_bytes(b"partial")
            completed = downloads / "song.mp3"
            completed.write_bytes(b"complete")
            ns = dict(os=os, LOGGER=Mock(), DOWNLOAD_DIR=str(downloads),
                CACHE_DIR=str(base / "cache"), COUPLE_DIR=str(base / "couples"))
            exec(compile(ast.Module(body=nodes, type_ignores=[]), "dir.py", "exec"), ns)
            previous = Path.cwd()
            try:
                os.chdir(base)
                ns["dirr"]()
            finally:
                os.chdir(previous)
            self.assertEqual(logo.read_bytes(), b"user image")
            self.assertTrue(completed.is_file())
            self.assertFalse(partial.exists())
            self.assertTrue((base / "cache").is_dir())


if __name__ == "__main__":
    unittest.main()
