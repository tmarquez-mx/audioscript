import os
import tempfile
import unittest
from unittest.mock import patch

import media


class MediaRecoveryTest(unittest.TestCase):
    def test_split_audio_repairs_source_after_decode_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = os.path.join(tmp_dir, "audio_danado.mp3")
            repaired_path = os.path.join(tmp_dir, "audio_reparado.wav")
            output_dir = os.path.join(tmp_dir, "chunks")
            output_chunk = os.path.join(output_dir, "chunk_001.mp3")
            for path in (source_path, repaired_path):
                with open(path, "wb") as handle:
                    handle.write(b"audio")

            with (
                patch.object(
                    media,
                    "get_media_metadata",
                    return_value={"duration_seconds": 120},
                ),
                patch.object(
                    media,
                    "split_media",
                    side_effect=[RuntimeError("decode error"), [output_chunk]],
                ) as split_mock,
                patch.object(
                    media,
                    "_repair_audio_source",
                    return_value=repaired_path,
                ) as repair_mock,
            ):
                chunks = media.split_audio(source_path, 5, output_dir)

            self.assertEqual(chunks, [output_chunk])
            self.assertEqual(split_mock.call_count, 2)
            repair_mock.assert_called_once_with(source_path)
            self.assertFalse(os.path.exists(repaired_path))


if __name__ == "__main__":
    unittest.main()
