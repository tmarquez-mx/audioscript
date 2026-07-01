import unittest
from unittest.mock import patch

import transcribe


ATTENTION_SHAPE_ERROR = (
    "cannot reshape tensor of 0 elements into shape [1, 0, 16, -1] because "
    "the unspecified dimension size -1 can be any value and is ambiguous"
)


class FakeWhisperModel:
    def __init__(self, should_fail):
        self.should_fail = should_fail

    def transcribe(self, *_args, **_kwargs):
        if self.should_fail:
            raise RuntimeError(ATTENTION_SHAPE_ERROR)
        return {"text": "recuperado"}


class WhisperRecoveryTest(unittest.TestCase):
    def setUp(self):
        transcribe.load_whisper_model.clear()
        transcribe.get_whisper_model_lock.clear()

    def tearDown(self):
        transcribe.load_whisper_model.clear()
        transcribe.get_whisper_model_lock.clear()

    def test_reloads_once_after_attention_shape_error(self):
        loads = []

        def fake_loader(_model_name, download_root=None):
            loads.append(True)
            return FakeWhisperModel(should_fail=len(loads) == 1)

        with patch.object(transcribe.whisper, "load_model", side_effect=fake_loader):
            result = transcribe.transcribe_audio(
                "archivo-simulado.mp3",
                "small",
                "Español",
            )

        self.assertEqual(result, "recuperado")
        self.assertEqual(len(loads), 2)


if __name__ == "__main__":
    unittest.main()
