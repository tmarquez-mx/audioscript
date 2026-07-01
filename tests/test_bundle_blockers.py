import os
import stat
import tempfile
import unittest
from unittest.mock import patch

import media
import transcribe
from shared_config import MODE_COMPLETE, normalize_processing_mode


class BundleBlockersTest(unittest.TestCase):
    def setUp(self):
        self.original_path = os.environ.get("PATH", "")
        transcribe.load_whisper_model.clear()
        media.configure_ffmpeg.cache_clear()

    def tearDown(self):
        os.environ["PATH"] = self.original_path
        os.environ.pop("AUDIOSCRIPT_APP_SUPPORT_DIR", None)
        os.environ.pop("AUDIOSCRIPT_FFMPEG_PATH", None)
        transcribe.load_whisper_model.clear()
        media.configure_ffmpeg.cache_clear()

    def test_load_whisper_model_is_cached(self):
        calls = []

        def fake_loader(model_name, download_root=None):
            calls.append((model_name, download_root))
            return {"model": model_name, "download_root": download_root}

        with patch.object(transcribe.whisper, "load_model", side_effect=fake_loader):
            first = transcribe.load_whisper_model("medium")
            second = transcribe.load_whisper_model("medium")

        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)

    def test_ensure_whisper_model_installed_skips_download_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["AUDIOSCRIPT_APP_SUPPORT_DIR"] = tmp_dir
            existing_path = transcribe.get_whisper_model_path("medium")
            os.makedirs(os.path.dirname(existing_path), exist_ok=True)
            with open(existing_path, "wb") as handle:
                handle.write(b"already-installed")

            callbacks = []

            with patch.object(transcribe.whisper, "_download") as mock_download:
                installed_path = transcribe.ensure_whisper_model_installed(
                    "medium",
                    lambda stage, message: callbacks.append((stage, message)),
                )

            self.assertEqual(installed_path, existing_path)
            self.assertFalse(mock_download.called)
            self.assertTrue(any(stage == "complete" for stage, _ in callbacks))

    def test_ensure_whisper_model_installed_downloads_into_app_support(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["AUDIOSCRIPT_APP_SUPPORT_DIR"] = tmp_dir
            callbacks = []

            def fake_download(model_url, target_dir, _in_memory):
                target_path = os.path.join(target_dir, os.path.basename(model_url))
                os.makedirs(target_dir, exist_ok=True)
                with open(target_path, "wb") as handle:
                    handle.write(b"downloaded-model")

            with patch.object(transcribe.whisper, "_download", side_effect=fake_download):
                installed_path = transcribe.ensure_whisper_model_installed(
                    "medium",
                    lambda stage, message: callbacks.append((stage, message)),
                )

            self.assertTrue(installed_path.startswith(tmp_dir))
            self.assertTrue(os.path.isfile(installed_path))
            self.assertTrue(any(stage == "download" for stage, _ in callbacks))
            self.assertTrue(any(stage == "verify" for stage, _ in callbacks))
            self.assertTrue(any(stage == "complete" for stage, _ in callbacks))

    def test_configure_ffmpeg_uses_dynamic_env_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_ffmpeg = os.path.join(tmp_dir, "custom-ffmpeg")
            with open(custom_ffmpeg, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\nexit 0\n")
            os.chmod(
                custom_ffmpeg,
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP,
            )
            os.environ["AUDIOSCRIPT_FFMPEG_PATH"] = custom_ffmpeg

            resolved = media.configure_ffmpeg()

            self.assertTrue(resolved)
            self.assertEqual(os.path.basename(resolved), "ffmpeg")
            self.assertTrue(os.path.exists(resolved))
            self.assertIn(os.path.dirname(resolved), os.environ["PATH"])

    def test_normalize_processing_mode_accepts_modo_completo(self):
        self.assertEqual(normalize_processing_mode("modo completo"), MODE_COMPLETE)
        self.assertEqual(normalize_processing_mode("Completo"), MODE_COMPLETE)


if __name__ == "__main__":
    unittest.main()
