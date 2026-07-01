import os
import re


BYTES_PER_MB = 1024 * 1024
AUDIO_SEGMENT_FORMAT = "mp3"
AUDIO_SEGMENT_CHANNELS = "1"
AUDIO_SEGMENT_SAMPLE_RATE = "16000"
AUDIO_SEGMENT_BITRATE = "128k"

MODE_SEGMENTED = "Segmentado"
MODE_COMPLETE = "Completo"
PROCESSING_MODES = (MODE_SEGMENTED, MODE_COMPLETE)

LANGUAGE_SPANISH = "Español"
LANGUAGE_AUTO = "Automático"
LANGUAGE_ENGLISH = "Inglés"
LANGUAGE_PORTUGUESE = "Portugués"
DEFAULT_TRANSCRIPTION_LANGUAGE = LANGUAGE_SPANISH
DEFAULT_WHISPER_MODEL = "medium"
GUIDED_INSTALL_MODEL_OPTIONS = ("medium", "large")
TRANSCRIPTION_LANGUAGES = (
    LANGUAGE_SPANISH,
    LANGUAGE_AUTO,
    LANGUAGE_ENGLISH,
    LANGUAGE_PORTUGUESE,
)
WHISPER_LANGUAGE_MAP = {
    "Detección automática": None,
    LANGUAGE_AUTO: None,
    LANGUAGE_SPANISH: "es",
    LANGUAGE_ENGLISH: "en",
    LANGUAGE_PORTUGUESE: "pt",
    "Auto": None,
}


def normalize_processing_mode(value):
    """Convierte etiquetas históricas o variantes de UI al modo canónico."""
    normalized = str(value or "").strip().casefold()
    if "complet" in normalized:
        return MODE_COMPLETE
    return MODE_SEGMENTED


def sanitize_filename(
    filename,
    preserve_extension=False,
    default_name="archivo",
    default_extension="",
):
    """Normaliza nombres para ids internos, rutas y salidas de ffmpeg."""
    raw_value = str(filename or "")
    if preserve_extension:
        name, extension = os.path.splitext(raw_value)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or default_name
        return f"{safe_name}{extension or default_extension}"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_value).strip("._") or default_name
    return safe_name
