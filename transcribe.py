import os
import threading
from urllib.parse import urlparse

import streamlit as st
import whisper

from media import configure_ffmpeg
from shared_config import DEFAULT_WHISPER_MODEL, WHISPER_LANGUAGE_MAP

try:
    import certifi
except ImportError:
    certifi = None


APP_SUPPORT_FOLDER = "AudioScript Contextual"
WHISPER_MODELS_FOLDER = "whisper_models"
WHISPER_MODEL_DOWNLOAD_SIZES = {
    "medium": "1.5 GB",
    "large": "3 GB",
}


def get_app_support_dir():
    """Devuelve la carpeta local estable de AudioScript en macOS."""
    custom_dir = os.environ.get("AUDIOSCRIPT_APP_SUPPORT_DIR", "").strip()
    support_dir = custom_dir or os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        APP_SUPPORT_FOLDER,
    )
    os.makedirs(support_dir, exist_ok=True)
    return support_dir


def get_whisper_models_dir():
    """Centraliza la ubicación de modelos para evitar cachés dispersas."""
    models_dir = os.path.join(get_app_support_dir(), WHISPER_MODELS_FOLDER)
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def get_whisper_model_url(model_name):
    return whisper._MODELS.get(str(model_name or DEFAULT_WHISPER_MODEL).strip().lower())


def get_whisper_model_path(model_name):
    model_url = get_whisper_model_url(model_name)
    if not model_url:
        return ""
    return os.path.join(get_whisper_models_dir(), os.path.basename(urlparse(model_url).path))


def is_whisper_model_installed(model_name):
    model_path = get_whisper_model_path(model_name)
    return bool(model_path and os.path.isfile(model_path) and os.path.getsize(model_path) > 0)


def get_whisper_model_installation_info(model_name):
    model_name = str(model_name or DEFAULT_WHISPER_MODEL).strip().lower()
    model_path = get_whisper_model_path(model_name)
    size_bytes = os.path.getsize(model_path) if model_path and os.path.isfile(model_path) else 0
    return {
        "model": model_name,
        "installed": bool(model_path and os.path.isfile(model_path)),
        "path": model_path,
        "size_bytes": size_bytes,
        "size_label": WHISPER_MODEL_DOWNLOAD_SIZES.get(model_name, ""),
    }


def ensure_whisper_model_installed(model_name, progress_callback=None):
    """Descarga una sola vez el modelo en la carpeta local de la app."""
    configure_ssl_certificates()
    model_name = str(model_name or DEFAULT_WHISPER_MODEL).strip().lower()
    model_url = get_whisper_model_url(model_name)
    if not model_url:
        raise RuntimeError(f"El modelo '{model_name}' no está disponible en esta versión de Whisper.")

    models_dir = get_whisper_models_dir()
    model_path = get_whisper_model_path(model_name)

    if progress_callback:
        progress_callback("prepare", "Preparando carpeta local del modelo…")

    if is_whisper_model_installed(model_name):
        if progress_callback:
            progress_callback("complete", f"El modelo {model_name} ya estaba instalado.")
        return model_path

    if progress_callback:
        progress_callback("download", f"Descargando modelo {model_name} por única vez…")
    whisper._download(model_url, models_dir, False)

    if progress_callback:
        progress_callback("verify", "Verificando integridad del archivo descargado…")
    if not is_whisper_model_installed(model_name):
        raise RuntimeError(
            "La descarga del modelo terminó, pero el archivo no quedó disponible en la carpeta local."
        )

    if progress_callback:
        progress_callback("complete", f"Modelo {model_name} instalado correctamente.")
    return model_path


def configure_ssl_certificates():
    """Ayuda a Python a encontrar certificados raiz al descargar modelos."""
    if certifi is None:
        return

    certificate_path = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", certificate_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certificate_path)

def build_initial_prompt(custom_terms, transcription_type):
    """Construye un prompt inicial para mejorar precisión contextual."""
    prompt_parts = []
    if "Verbatim" in transcription_type:
        prompt_parts.append(
            "Transcripcion literal de entrevista, conserva muletillas, pausas y repeticiones."
        )
    else:
        prompt_parts.append(
            "Transcripcion limpia de entrevista, conserva sentido y claridad del habla."
        )

    if custom_terms.strip():
        prompt_parts.append(f"Terminos y nombres relevantes: {custom_terms.strip()}")

    return " ".join(prompt_parts).strip()

@st.cache_resource(show_spinner=False, max_entries=3)
def load_whisper_model(model_name):
    """Carga una sola instancia reutilizable del modelo Whisper seleccionado."""
    return whisper.load_model(model_name, download_root=get_whisper_models_dir())


@st.cache_resource(show_spinner=False)
def get_whisper_model_lock(model_name):
    """Evita que dos reruns usen simultáneamente el mismo modelo mutable."""
    return threading.RLock()


def is_whisper_attention_shape_error(exc):
    error_text = str(exc).casefold()
    return (
        "cannot reshape tensor of 0 elements" in error_text
        and "unspecified dimension size -1" in error_text
    )

def transcribe_audio(
    file_path,
    model_name,
    language_choice="Detección automática",
    custom_terms="",
    transcription_type="Limpia (Sin muletillas)",
):
    """Realiza la transcripción usando Whisper con contexto personalizado."""
    configure_ssl_certificates()
    if not configure_ffmpeg():
        raise RuntimeError(
            "No pude localizar ffmpeg para preparar el audio antes de transcribir."
        )
    try:
        model = load_whisper_model(model_name)
    except Exception as exc:
        error_text = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" in error_text or "certificate verify failed" in error_text:
            raise RuntimeError(
                "No pude descargar o verificar el modelo de Whisper por un problema de certificados SSL. "
                "Suele ocurrir en redes institucionales con filtros de seguridad. Prueba otra red, "
                "activa una conexión personal o instala el modelo previamente en esta Mac."
            ) from exc
        raise
    options = {}

    language = WHISPER_LANGUAGE_MAP.get(language_choice)
    if language:
        options["language"] = language

    initial_prompt = build_initial_prompt(custom_terms, transcription_type)
    if initial_prompt:
        options["initial_prompt"] = initial_prompt

    model_lock = get_whisper_model_lock(model_name)
    with model_lock:
        try:
            result = model.transcribe(file_path, **options)
        except RuntimeError as exc:
            if not is_whisper_attention_shape_error(exc):
                raise

            # Un modelo compartido puede quedar en un estado transitorio si dos
            # reruns intentan usarlo a la vez. Se reconstruye una sola vez.
            load_whisper_model.clear()
            model = load_whisper_model(model_name)
            retry_options = {**options, "condition_on_previous_text": False}
            try:
                result = model.transcribe(file_path, **retry_options)
            except RuntimeError as retry_exc:
                if is_whisper_attention_shape_error(retry_exc):
                    raise RuntimeError(
                        "Whisper no pudo procesar este fragmento. Vuelve a dividir el material "
                        "o prueba un segmento más corto."
                    ) from retry_exc
                raise
    return result["text"]
