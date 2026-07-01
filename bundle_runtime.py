"""Punto de entrada congelado para el bundle macOS de AudioScript Contextual."""

import json
import os
import platform
import sys
from pathlib import Path

# Imports explícitos para que PyInstaller incluya todas las funciones de la app.
import certifi  # noqa: F401
import docx  # noqa: F401
import imageio_ffmpeg  # noqa: F401
import numpy  # noqa: F401
import openpyxl  # noqa: F401
import pandas  # noqa: F401
import torch  # noqa: F401
import whisper  # noqa: F401


def resources_dir():
    configured = os.environ.get("AUDIOSCRIPT_RESOURCES_DIR", "").strip()
    if configured:
        return Path(configured).resolve()
    return Path(sys.executable).resolve().parent.parent


def run_self_test():
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    docx_templates_dir = Path(docx.__file__).resolve().parent / "templates"
    checks = {
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "ffmpeg": ffmpeg_path,
        "ffmpeg_exists": Path(ffmpeg_path).is_file(),
        "app_exists": (resources_dir() / "App.py").is_file(),
        "docx_templates": (docx_templates_dir / "default-footer.xml").is_file(),
    }
    print(json.dumps(checks, ensure_ascii=False))
    return 0 if checks["architecture"] == "arm64" and all(
        checks[key] for key in ("ffmpeg_exists", "app_exists", "docx_templates")
    ) else 1


def run_streamlit():
    app_path = resources_dir() / "App.py"
    port = os.environ.get("AUDIOSCRIPT_STREAMLIT_PORT", "8501")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false",
        "--client.toolbarMode=minimal",
        "--theme.base=light",
        "--server.address=localhost",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.maxUploadSize=2048",
        "--browser.serverAddress=localhost",
    ]
    from streamlit.web.cli import main

    main(prog_name="streamlit")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())
    raise SystemExit(run_streamlit())
