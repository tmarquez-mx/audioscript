import os
import re
import json
import html
import shutil
import subprocess
import tempfile
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st
import whisper
import streamlit.components.v1 as components
from docx import Document
from docx.shared import Pt
from pydub import AudioSegment


st.set_page_config(page_title="Audioscript Contextual Pro", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f7f3cd 0%, #fbf9e8 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f8fb 0%, #ffffff 100%);
        border-right: 1px solid rgba(20, 46, 83, 0.08);
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem;
    }
    .app-shell {
        padding-bottom: 1rem;
    }
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.25rem 1.5rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #163a63 0%, #3d6d9b 100%);
        color: white;
        box-shadow: 0 14px 35px rgba(20, 46, 83, 0.18);
        margin-bottom: 1rem;
    }
    .app-header__brand {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .app-logo {
        width: 74px;
        height: 44px;
        border-radius: 10px;
        background: linear-gradient(135deg, #0b1f38 0%, #1f4f7b 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-align: center;
        line-height: 1.1;
        border: 1px solid rgba(255,255,255,0.18);
    }
    .app-header h1 {
        font-size: 1.8rem;
        margin: 0;
        color: white;
    }
    .app-header p {
        margin: 0.1rem 0 0 0;
        opacity: 0.9;
        font-size: 0.98rem;
    }
    .header-actions {
        display: flex;
        gap: 0.65rem;
        align-items: center;
    }
    .header-pill {
        width: 36px;
        height: 36px;
        border-radius: 999px;
        background: rgba(255,255,255,0.18);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
    }
    .section-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(20, 46, 83, 0.08);
        box-shadow: 0 8px 24px rgba(40, 52, 89, 0.08);
        border-radius: 16px;
        padding: 1rem 1rem 0.85rem 1rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #2b3443;
        margin-bottom: 0.75rem;
    }
    .mini-stat-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 0.8rem;
    }
    .mini-stat {
        background: #f4f7fb;
        border: 1px solid rgba(20, 46, 83, 0.08);
        border-radius: 12px;
        padding: 0.75rem;
    }
    .mini-stat__label {
        color: #6b7280;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .mini-stat__value {
        color: #17324f;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0.2rem;
    }
    .project-card {
        border: 1px solid rgba(20, 46, 83, 0.12);
        border-radius: 14px;
        background: white;
        padding: 0.75rem;
        margin-bottom: 0.65rem;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.3);
    }
    .project-card strong {
        color: #24364a;
        display: block;
        margin-bottom: 0.15rem;
    }
    .project-card span {
        color: #6b7280;
        font-size: 0.84rem;
    }
    .footer-bar {
        position: sticky;
        bottom: 0;
        margin-top: 1rem;
        border-radius: 12px 12px 0 0;
        background: #e91e3e;
        color: white;
        text-align: center;
        padding: 0.55rem 1rem;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .circle-status-card {
        background: white;
        border: 1px solid rgba(20, 46, 83, 0.08);
        border-radius: 18px;
        padding: 0.85rem 0.75rem 1rem 0.75rem;
        text-align: center;
        box-shadow: 0 8px 22px rgba(30, 41, 59, 0.08);
        margin-bottom: 0.9rem;
    }
    .circle-shell {
        width: 110px;
        height: 110px;
        margin: 0 auto 0.7rem auto;
        border-radius: 999px;
        background: radial-gradient(circle at 50% 50%, #f8f4d3 0 39%, #4d82b6 41%, #173d67 100%);
        border: 6px solid rgba(255,255,255,0.9);
        box-shadow: 0 10px 22px rgba(20, 46, 83, 0.16);
        display: grid;
        place-items: center;
        position: relative;
    }
    .circle-shell::after {
        content: "";
        position: absolute;
        width: 84px;
        height: 84px;
        border-radius: 999px;
        border: 3px solid rgba(123, 97, 255, 0.18);
        box-shadow: 0 0 18px rgba(123, 97, 255, 0.22);
    }
    .circle-core {
        position: relative;
        z-index: 1;
        min-width: 66px;
        padding: 0.3rem 0.55rem;
        border-radius: 10px;
        background: #0f2f53;
        color: white;
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1.15;
    }
    .circle-label {
        font-size: 0.78rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .circle-value {
        font-size: 1.35rem;
        color: #7c4de1;
        font-weight: 800;
        margin-top: 0.3rem;
    }
    .dial-card {
        background: white;
        border: 1px solid rgba(20, 46, 83, 0.08);
        border-radius: 18px;
        padding: 0.85rem 0.75rem 1rem 0.75rem;
        text-align: center;
        box-shadow: 0 8px 22px rgba(30, 41, 59, 0.08);
        margin-bottom: 0.9rem;
    }
    .dial-face {
        width: 118px;
        height: 118px;
        margin: 0.2rem auto 0.75rem auto;
        border-radius: 999px;
        background: radial-gradient(circle at 50% 50%, #f8f4d3 0 38%, #4d82b6 40%, #173d67 100%);
        border: 6px solid rgba(255,255,255,0.92);
        box-shadow: 0 10px 22px rgba(20, 46, 83, 0.16);
        display: grid;
        place-items: center;
    }
    .dial-center {
        min-width: 70px;
        padding: 0.35rem 0.55rem;
        border-radius: 10px;
        background: #0f2f53;
        color: white;
        font-size: 0.95rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .dial-title {
        font-size: 0.78rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.45rem;
    }
    .dial-current {
        font-size: 1.2rem;
        color: #7c4de1;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .main-title {
        font-size: 28px !important;
        font-weight: 700;
        color: #1E1E1E;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 16px !important;
        color: #555;
        margin-bottom: 24px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        border: none;
        box-shadow: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


TEMP_DIR = os.path.join(tempfile.gettempdir(), "audioscript_contextual")
os.makedirs(TEMP_DIR, exist_ok=True)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(APP_DIR, ".audioscript_projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)
HEADER_REFERENCE_PATH = os.path.join(APP_DIR, "assets", "header_reference.png")

LANGUAGE_MAP = {
    "Detección automática": None,
    "Español": "es",
    "Inglés": "en",
    "Auto": None,
}


def apply_editor_styles(font_size_px):
    """Ajusta el tamano de letra de las areas principales de transcripcion."""
    st.markdown(
        f"""
        <style>
        textarea[aria-label="Edite este fragmento antes de continuar"],
        textarea[aria-label="Edite el texto si es necesario"],
        textarea[aria-label="Contenido consolidado"] {{
            font-size: {font_size_px}px !important;
            line-height: 1.6 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    """Dibuja una cabecera cercana al mockup de referencia."""
    if os.path.exists(HEADER_REFERENCE_PATH):
        st.image(HEADER_REFERENCE_PATH, use_container_width=True)
        return

    st.markdown(
        """
        <div class="app-shell">
          <div class="app-header">
            <div class="app-header__brand">
              <div class="app-logo">AUDIOSCRIPT<br>CONTEXTUAL</div>
              <div>
                <h1>AudioScript Contextual</h1>
                <p>Transcripción inmersiva potenciada por IA</p>
              </div>
            </div>
            <div class="header-actions">
              <span class="header-pill">☼</span>
              <span class="header-pill">◐</span>
              <span class="header-pill">☾</span>
              <span class="header-pill">⚙</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_circle(label, value, note=""):
    st.markdown(
        f"""
        <div class="circle-status-card">
          <div class="circle-shell">
            <div class="circle-core">{value}</div>
          </div>
          <div class="circle-label">{label}</div>
          <div class="circle-value">{value}</div>
          <div style="font-size:10px;color:#7a7f87;line-height:1.35;margin-top:0.35rem;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def select_dial_option(label, current_value, options, key_prefix):
    """Dibuja un selector circular con opciones en posiciones tipo reloj."""
    st.markdown(
        f"""
        <div class="dial-card">
          <div class="dial-title">{label}</div>
          <div class="dial-face"><div class="dial-center">{current_value}</div></div>
          <div class="dial-current">Selecciona</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    layout = [
        [None, options[0], None],
        [options[4], None, options[1]],
        [options[3], None, options[2]],
    ]

    for row_idx, row in enumerate(layout):
        cols = st.columns(3)
        for col_idx, option in enumerate(row):
            with cols[col_idx]:
                if option is None:
                    st.write("")
                    continue
                selected = option == current_value
                button_label = f"* {option}" if selected else option
                if st.button(
                    button_label,
                    key=f"{key_prefix}_{row_idx}_{col_idx}_{option}",
                    help=f"Usar {option}",
                ):
                    return option

    return current_value


def render_font_size_dial():
    """Controla el tamano de letra desde un dial compacto."""
    current_size = st.session_state.sidebar_editor_font_size
    st.markdown(
        f"""
        <div class="dial-card">
          <div class="dial-title">Tamaño de letra</div>
          <div class="dial-face"><div class="dial-center">{current_size}px</div></div>
          <div class="dial-current">Editor</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    minus_col, value_col, plus_col = st.columns([1, 1.4, 1])
    with minus_col:
        if st.button("- 1", key="font_size_minus"):
            st.session_state.sidebar_editor_font_size = max(12, current_size - 1)
            st.rerun()
    with value_col:
        st.number_input(
            "Tamaño",
            min_value=12,
            max_value=28,
            step=1,
            key="sidebar_editor_font_size",
            label_visibility="collapsed",
        )
    with plus_col:
        if st.button("+ 1", key="font_size_plus"):
            st.session_state.sidebar_editor_font_size = min(28, current_size + 1)
            st.rerun()

    return st.session_state.sidebar_editor_font_size


def open_card(title):
    st.markdown(
        f'<div class="section-card"><div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )


def close_card():
    st.markdown("</div>", unsafe_allow_html=True)


def render_selectable_transcript_panel(text, highlight_term=""):
    """Muestra el texto transcrito como bloque seleccionable para codificar con mouse."""
    safe_text = html.escape(text or "Aún no hay texto transcrito en este segmento.")
    if highlight_term.strip():
        pattern = re.compile(re.escape(html.escape(highlight_term.strip())), re.IGNORECASE)
        safe_text = pattern.sub(
            lambda match: (
                "<mark style='background:#ffe58a;color:#1f2937;padding:0 2px;border-radius:3px;'>"
                f"{match.group(0)}</mark>"
            ),
            safe_text,
        )
    safe_text = safe_text.replace("\n", "<br>")
    components.html(
        f"""
        <div id="selection-wrap" style="position:relative;">
          <div id="selection-toolbar" style="display:none; position:absolute; top:10px; right:10px; z-index:20;">
            <button id="selection-code-btn" style="
              border:none;
              background:#17324f;
              color:white;
              padding:8px 12px;
              border-radius:999px;
              font-size:12px;
              cursor:pointer;
              box-shadow:0 8px 18px rgba(23,50,79,.25);
            ">Codificar selección</button>
          </div>
          <div id="selectable-transcript" style="
            min-height:220px;
            max-height:340px;
            overflow:auto;
            background:#ffffff;
            border:1px solid rgba(20,46,83,.12);
            border-radius:14px;
            padding:16px 18px;
            color:#263238;
            font-size:15px;
            line-height:1.75;
            white-space:normal;
            user-select:text;
          ">{safe_text}</div>
        </div>
        <script>
        const parentDoc = window.parent.document;
        const transcriptEl = document.getElementById("selectable-transcript");
        const toolbarEl = document.getElementById("selection-toolbar");
        const codeButtonEl = document.getElementById("selection-code-btn");
        let currentSelection = "";

        function setStreamlitField(label, value) {{
          const target = parentDoc.querySelector(`textarea[aria-label="${{label}}"], input[aria-label="${{label}}"]`);
          if (!target) return false;
          const nativeSetter = Object.getOwnPropertyDescriptor(
            target.tagName === "TEXTAREA"
              ? window.HTMLTextAreaElement.prototype
              : window.HTMLInputElement.prototype,
            "value"
          ).set;
          nativeSetter.call(target, value);
          target.dispatchEvent(new Event("input", {{ bubbles: true }}));
          target.dispatchEvent(new Event("change", {{ bubbles: true }}));
          return true;
        }}

        function focusCodeField() {{
          const codeField = parentDoc.querySelector('input[aria-label="Código"]');
          if (codeField) codeField.focus();
        }}

        function updateSelection() {{
          const selection = window.getSelection();
          const selectedText = selection ? selection.toString().trim() : "";
          if (selectedText && transcriptEl.contains(selection.anchorNode)) {{
            currentSelection = selectedText;
            toolbarEl.style.display = "block";
          }} else {{
            currentSelection = "";
            toolbarEl.style.display = "none";
          }}
        }}

        transcriptEl.addEventListener("mouseup", updateSelection);
        transcriptEl.addEventListener("keyup", updateSelection);
        transcriptEl.addEventListener("touchend", updateSelection);

        codeButtonEl.addEventListener("click", function() {{
          if (!currentSelection) return;
          const updated = setStreamlitField("Cita o frase a codificar", currentSelection);
          if (updated) {{
            focusCodeField();
          }}
        }});
        </script>
        """,
        height=360,
    )


def build_project_id(uploaded_file):
    """Crea un identificador estable para el proyecto del archivo cargado."""
    raw_id = f"{uploaded_file.name}-{uploaded_file.size}"
    return hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:16]


def get_project_dir(project_id):
    return os.path.join(PROJECTS_DIR, project_id)


def get_project_state_path(project_id):
    return os.path.join(get_project_dir(project_id), "state.json")


def get_project_chunks_dir(project_id):
    return os.path.join(get_project_dir(project_id), "chunks")


def get_project_audio_path(project_id, original_name):
    extension = os.path.splitext(original_name)[1] or ".audio"
    return os.path.join(get_project_dir(project_id), f"source{extension}")


def save_uploaded_file(uploaded_file, destination_path):
    """Guarda el archivo cargado en una ruta reutilizable."""
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with open(destination_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
    return destination_path


def init_session_state():
    defaults = {
        "uploaded_file_id": None,
        "current_project_id": None,
        "chunks": [],
        "chunks_prepared": False,
        "chunk_segment_mins": None,
        "current_chunk_idx": 0,
        "transcript_segments": [],
        "current_segment_text": "",
        "memos": [],
        "codes": [],
        "last_transcription": "",
        "autosave_last_saved": "",
        "sidebar_mode": "Segmentado (Recomendación para transcripciones cualitativas)",
        "sidebar_model_choice": "base",
        "sidebar_language_choice": "Detección automática",
        "sidebar_trans_type": "Limpia (Sin muletillas)",
        "sidebar_segment_mins": 5,
        "sidebar_editor_font_size": 16,
        "main_doc_title": "Transcripcion",
        "main_event_date": datetime.now().date(),
        "main_transcription_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "main_custom_terms": "",
        "pending_segment_action": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_transcription_state():
    st.session_state.chunks = []
    st.session_state.chunks_prepared = False
    st.session_state.chunk_segment_mins = None
    st.session_state.current_chunk_idx = 0
    st.session_state.transcript_segments = []
    st.session_state.current_segment_text = ""
    st.session_state.pending_segment_action = None
    st.session_state.memos = []
    st.session_state.codes = []
    st.session_state.last_transcription = ""


def check_ffmpeg():
    """Verifica si ffmpeg está disponible en el sistema."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def initialize_project_defaults(uploaded_file):
    """Carga valores iniciales cuando no existe un proyecto previo."""
    st.session_state.main_doc_title = os.path.splitext(uploaded_file.name)[0] or "Entrevista_01"
    st.session_state.main_event_date = datetime.now().date()
    st.session_state.main_transcription_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.session_state.main_custom_terms = ""
    st.session_state.sidebar_mode = "Segmentado (Recomendación para transcripciones cualitativas)"
    st.session_state.sidebar_model_choice = "base"
    st.session_state.sidebar_language_choice = "Detección automática"
    st.session_state.sidebar_trans_type = "Limpia (Sin muletillas)"
    st.session_state.sidebar_segment_mins = 5
    st.session_state.sidebar_editor_font_size = 16


def load_project_state(project_id):
    """Lee el estado guardado de un proyecto si existe."""
    state_path = get_project_state_path(project_id)
    if not os.path.exists(state_path):
        return None

    with open(state_path, "r", encoding="utf-8") as state_file:
        return json.load(state_file)


def apply_project_state(project_state):
    """Restaura el estado serializado en session_state."""
    st.session_state.sidebar_mode = project_state.get(
        "sidebar_mode",
        st.session_state.sidebar_mode,
    )
    st.session_state.sidebar_model_choice = project_state.get(
        "sidebar_model_choice",
        st.session_state.sidebar_model_choice,
    )
    st.session_state.sidebar_language_choice = project_state.get(
        "sidebar_language_choice",
        st.session_state.sidebar_language_choice,
    )
    st.session_state.sidebar_trans_type = project_state.get(
        "sidebar_trans_type",
        st.session_state.sidebar_trans_type,
    )
    st.session_state.sidebar_segment_mins = project_state.get(
        "sidebar_segment_mins",
        st.session_state.sidebar_segment_mins,
    )
    st.session_state.sidebar_editor_font_size = project_state.get(
        "sidebar_editor_font_size",
        st.session_state.sidebar_editor_font_size,
    )
    st.session_state.main_doc_title = project_state.get(
        "main_doc_title",
        st.session_state.main_doc_title,
    )
    saved_event_date = project_state.get("main_event_date")
    if saved_event_date:
        st.session_state.main_event_date = datetime.fromisoformat(saved_event_date).date()
    st.session_state.main_transcription_date = project_state.get(
        "main_transcription_date",
        st.session_state.main_transcription_date,
    )
    st.session_state.main_custom_terms = project_state.get(
        "main_custom_terms",
        st.session_state.main_custom_terms,
    )
    st.session_state.current_chunk_idx = project_state.get("current_chunk_idx", 0)
    st.session_state.transcript_segments = project_state.get("transcript_segments", [])
    st.session_state.current_segment_text = project_state.get("current_segment_text", "")
    st.session_state.memos = project_state.get("memos", [])
    st.session_state.codes = project_state.get("codes", [])
    st.session_state.last_transcription = project_state.get("last_transcription", "")
    st.session_state.chunks_prepared = project_state.get("chunks_prepared", False)
    st.session_state.chunk_segment_mins = project_state.get("chunk_segment_mins")
    st.session_state.autosave_last_saved = project_state.get("autosave_last_saved", "")


def save_project_state():
    """Guarda automáticamente el avance del proyecto actual."""
    project_id = st.session_state.get("current_project_id")
    uploaded_file_id = st.session_state.get("uploaded_file_id")
    if not project_id or not uploaded_file_id:
        return

    os.makedirs(get_project_dir(project_id), exist_ok=True)
    state = {
        "uploaded_file_id": uploaded_file_id,
        "sidebar_mode": st.session_state.sidebar_mode,
        "sidebar_model_choice": st.session_state.sidebar_model_choice,
        "sidebar_language_choice": st.session_state.sidebar_language_choice,
        "sidebar_trans_type": st.session_state.sidebar_trans_type,
        "sidebar_segment_mins": st.session_state.sidebar_segment_mins,
        "sidebar_editor_font_size": st.session_state.sidebar_editor_font_size,
        "main_doc_title": st.session_state.main_doc_title,
        "main_event_date": st.session_state.main_event_date.isoformat(),
        "main_transcription_date": st.session_state.main_transcription_date,
        "main_custom_terms": st.session_state.main_custom_terms,
        "current_chunk_idx": st.session_state.current_chunk_idx,
        "transcript_segments": st.session_state.transcript_segments,
        "current_segment_text": st.session_state.current_segment_text,
        "memos": st.session_state.memos,
        "codes": st.session_state.codes,
        "last_transcription": st.session_state.last_transcription,
        "chunks_prepared": st.session_state.chunks_prepared,
        "chunk_segment_mins": st.session_state.chunk_segment_mins,
        "autosave_last_saved": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    with open(get_project_state_path(project_id), "w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=True, indent=2)

    st.session_state.autosave_last_saved = state["autosave_last_saved"]


def delete_project_state(project_id):
    """Elimina estado y segmentos preparados del proyecto actual."""
    if not project_id:
        return

    state_path = get_project_state_path(project_id)
    chunks_dir = get_project_chunks_dir(project_id)
    if os.path.exists(state_path):
        os.remove(state_path)
    if os.path.isdir(chunks_dir):
        shutil.rmtree(chunks_dir)


def list_existing_chunks(project_id):
    """Recupera los chunks existentes en disco."""
    chunks_dir = get_project_chunks_dir(project_id)
    if not os.path.isdir(chunks_dir):
        return []

    chunk_files = [
        os.path.join(chunks_dir, filename)
        for filename in os.listdir(chunks_dir)
        if filename.startswith("chunk_")
    ]
    return sorted(chunk_files)


def restore_project_if_available(uploaded_file):
    """Restaura un proyecto previo o inicializa uno nuevo."""
    project_id = build_project_id(uploaded_file)
    uploaded_file_id = f"{uploaded_file.name}-{uploaded_file.size}"

    if (
        st.session_state.current_project_id == project_id
        and st.session_state.uploaded_file_id == uploaded_file_id
    ):
        return project_id

    reset_transcription_state()
    st.session_state.current_project_id = project_id
    st.session_state.uploaded_file_id = uploaded_file_id
    save_uploaded_file(
        uploaded_file,
        get_project_audio_path(project_id, uploaded_file.name),
    )

    saved_state = load_project_state(project_id)
    if saved_state:
        apply_project_state(saved_state)
    else:
        initialize_project_defaults(uploaded_file)

    return project_id


def build_initial_prompt(custom_terms, transcription_type):
    """Construye un prompt inicial para mejorar precisión contextual."""
    prompt_parts = []
    if transcription_type == "Verbatim (Literal - incluye errores)":
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


def transcribe_audio(
    file_path,
    model_name,
    language_choice="Detección automática",
    custom_terms="",
    transcription_type="Limpia (Sin muletillas)",
):
    """Realiza la transcripción usando Whisper con contexto personalizado."""
    model = whisper.load_model(model_name)
    options = {}

    language = LANGUAGE_MAP.get(language_choice)
    if language:
        options["language"] = language

    initial_prompt = build_initial_prompt(custom_terms, transcription_type)
    if initial_prompt:
        options["initial_prompt"] = initial_prompt

    result = model.transcribe(file_path, **options)
    return result["text"]


def split_audio(file_path, segment_mins, output_dir, output_format="wav"):
    """Divide el audio en fragmentos de N minutos."""
    audio = AudioSegment.from_file(file_path)
    segment_ms = int(segment_mins * 60 * 1000)
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    chunk_files = []

    for i, start_ms in enumerate(range(0, len(audio), segment_ms)):
        chunk = audio[start_ms : start_ms + segment_ms]
        chunk_path = os.path.join(output_dir, f"chunk_{i}.{output_format}")
        chunk.export(chunk_path, format=output_format)
        chunk_files.append(chunk_path)

    return chunk_files


def ensure_project_chunks(audio_path):
    """Restaura o reconstruye los segmentos si el proyecto ya tenía avance."""
    if not st.session_state.chunks_prepared:
        return

    existing_chunks = list_existing_chunks(st.session_state.current_project_id)
    if existing_chunks:
        st.session_state.chunks = existing_chunks
        return

    st.session_state.chunks = split_audio(
        audio_path,
        st.session_state.chunk_segment_mins or st.session_state.sidebar_segment_mins,
        get_project_chunks_dir(st.session_state.current_project_id),
    )


def render_segment_audio_player(audio_path):
    """Muestra el audio del segmento actual con saltos rapidos."""
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    extension = os.path.splitext(audio_path)[1].lower().replace(".", "") or "wav"
    audio_format = "audio/mpeg" if extension == "mp3" else f"audio/{extension}"
    st.audio(audio_bytes, format=audio_format)
    components.html(
        """
        <div style="display:flex; gap:8px; align-items:center; margin-top:4px; flex-wrap:wrap;">
          <button onclick="controlSegmentAudio(-5)" style="padding:6px 10px;">-5 s</button>
          <button onclick="toggleSegmentAudio()" style="padding:6px 10px;">Play / Pause</button>
          <button onclick="controlSegmentAudio(5)" style="padding:6px 10px;">+5 s</button>
          <span style="font-size:12px; color:#555;">Atajos: Alt + Flecha izquierda/derecha</span>
        </div>
        <script>
        function latestAudioElement() {
          const parentDoc = window.parent.document;
          const audios = parentDoc.querySelectorAll("audio");
          return audios[audios.length - 1];
        }
        function controlSegmentAudio(delta) {
          const audio = latestAudioElement();
          if (!audio) return;
          const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
          const nextTime = Math.max(0, Math.min(duration || Number.MAX_SAFE_INTEGER, audio.currentTime + delta));
          audio.currentTime = nextTime;
        }
        function toggleSegmentAudio() {
          const audio = latestAudioElement();
          if (!audio) return;
          if (audio.paused) {
            audio.play();
          } else {
            audio.pause();
          }
        }
        </script>
        """,
        height=58,
    )


def render_keyboard_shortcuts(segment_mode_active):
    """Activa atajos de teclado para acelerar la revisión."""
    confirm_label = "Confirmar y Siguiente" if segment_mode_active else "Iniciar Transcripción Completa"
    components.html(
        f"""
        <script>
        const parentWindow = window.parent;
        const parentDoc = parentWindow.document;
        parentWindow.__audioscriptShortcutConfig = {{
          confirmLabel: "{confirm_label}"
        }};

        if (!parentWindow.__audioscriptShortcutsBound) {{
          parentWindow.__audioscriptShortcutsBound = true;

          function findButton(label) {{
            return Array.from(parentDoc.querySelectorAll("button")).find(
              (button) => button.innerText.trim() === label
            );
          }}

          function clickButton(label) {{
            const button = findButton(label);
            if (button) {{
              button.click();
            }}
          }}

          function findTextArea(label) {{
            return parentDoc.querySelector(`textarea[aria-label="${{label}}"]`);
          }}

          function latestAudioElement() {{
            const audios = parentDoc.querySelectorAll("audio");
            return audios[audios.length - 1];
          }}

          function skipAudio(delta) {{
            const audio = latestAudioElement();
            if (!audio) return;
            const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
            const nextTime = Math.max(0, Math.min(duration || Number.MAX_SAFE_INTEGER, audio.currentTime + delta));
            audio.currentTime = nextTime;
          }}

          parentWindow.addEventListener("keydown", function(event) {{
            if (event.defaultPrevented) return;

            if (event.ctrlKey && event.key === "Enter") {{
              event.preventDefault();
              clickButton(parentWindow.__audioscriptShortcutConfig.confirmLabel);
              return;
            }}

            if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "t") {{
              event.preventDefault();
              clickButton("Transcribir este fragmento");
              return;
            }}

            if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "r") {{
              event.preventDefault();
              clickButton("Reiniciar segmento");
              return;
            }}

            if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "m") {{
              event.preventDefault();
              const memoBox = findTextArea("Nueva anotación");
              if (memoBox) memoBox.focus();
              return;
            }}

            if (event.altKey && event.key === "ArrowLeft") {{
              event.preventDefault();
              skipAudio(-5);
              return;
            }}

            if (event.altKey && event.key === "ArrowRight") {{
              event.preventDefault();
              skipAudio(5);
            }}
          }});
        }}
        </script>
        """,
        height=0,
    )


def add_formatted_transcript(doc, text):
    """Aplica formato simple al cuerpo de la transcripción."""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        speaker_label, spoken_text = extract_speaker_label(line)
        if speaker_label:
            paragraph = doc.add_paragraph()
            paragraph.add_run(speaker_label).bold = True
            if spoken_text:
                paragraph.add_run(f" {spoken_text}")
        else:
            doc.add_paragraph(line)


def extract_speaker_label(line):
    """Detecta etiquetas de hablante tipo 'Entrevistadora 1:' al inicio de línea."""
    prefix, separator, remainder = line.partition(":")
    candidate = prefix.strip()
    if not separator or not candidate:
        return None, None

    if len(candidate) > 48 or len(candidate.split()) > 6:
        return None, None

    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.\-_/()]+", candidate):
        return None, None

    return f"{candidate}:", remainder.strip()


def build_codes_dataframe():
    """Convierte los códigos guardados en un DataFrame exportable."""
    if not st.session_state.codes:
        return pd.DataFrame()
    return pd.DataFrame(st.session_state.codes)


def render_memo_manager(segment_number):
    """Permite crear, editar y eliminar memos del segmento actual."""
    st.markdown("### Memos de análisis")
    st.caption("Anotaciones rápidas para complementar la transcripción.")

    with st.form(key=f"memo_form_{segment_number}", clear_on_submit=True):
        memo_input = st.text_area(
            "Nueva anotación",
            key=f"memo_input_{segment_number}",
            height=140,
        )
        memo_submitted = st.form_submit_button("Guardar Memo")

    if memo_submitted:
        if memo_input.strip():
            st.session_state.memos.append(
                {"segmento": segment_number, "memo": memo_input.strip()}
            )
            save_project_state()
            st.rerun()
        st.warning("Escribe un memo antes de guardarlo.")

    st.markdown("---")
    current_segment_memos = [
        (memo_idx, memo)
        for memo_idx, memo in enumerate(st.session_state.memos)
        if memo["segmento"] == segment_number
    ]

    if not current_segment_memos:
        st.write("Todavía no hay memos para este segmento.")
        return

    for memo_idx, memo in current_segment_memos:
        with st.expander(f"Memo {memo_idx + 1}", expanded=False):
            with st.form(key=f"edit_memo_form_{segment_number}_{memo_idx}"):
                edited_memo = st.text_area(
                    "Editar memo",
                    value=memo["memo"],
                    height=120,
                )
                save_col, delete_col = st.columns(2)
                with save_col:
                    save_memo = st.form_submit_button("Guardar cambios")
                with delete_col:
                    delete_memo = st.form_submit_button("Eliminar memo")

            if save_memo:
                if edited_memo.strip():
                    st.session_state.memos[memo_idx]["memo"] = edited_memo.strip()
                    save_project_state()
                    st.rerun()
                st.warning("El memo no puede quedar vacío.")

            if delete_memo:
                st.session_state.memos.pop(memo_idx)
                save_project_state()
                st.rerun()


def render_code_manager(segment_number):
    """Permite crear, editar y eliminar codificaciones básicas por segmento."""
    st.markdown("### Codificación básica")
    st.caption("Pega la frase del segmento, asigna un código y guarda una nota opcional.")

    with st.form(key=f"code_form_{segment_number}", clear_on_submit=True):
        quote_text = st.text_area(
            "Cita o frase a codificar",
            key=f"code_quote_{segment_number}",
            height=120,
            placeholder="Pega aquí la frase exacta del segmento transcrito.",
        )
        code_label = st.text_input(
            "Código",
            key=f"code_label_{segment_number}",
            placeholder="Ej: identidad, conflicto, precariedad...",
        )
        code_note = st.text_area(
            "Nota analítica opcional",
            key=f"code_note_{segment_number}",
            height=100,
        )
        code_submitted = st.form_submit_button("Guardar código")

    if code_submitted:
        if quote_text.strip() and code_label.strip():
            st.session_state.codes.append(
                {
                    "segmento": segment_number,
                    "cita": quote_text.strip(),
                    "codigo": code_label.strip(),
                    "nota": code_note.strip(),
                    "fecha_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                }
            )
            save_project_state()
            st.rerun()
        st.warning("Completa al menos la cita y el nombre del código.")

    st.markdown("---")
    current_segment_codes = [
        (code_idx, code_item)
        for code_idx, code_item in enumerate(st.session_state.codes)
        if code_item["segmento"] == segment_number
    ]

    if not current_segment_codes:
        st.write("Todavía no hay códigos para este segmento.")
        return

    for code_idx, code_item in current_segment_codes:
        with st.expander(f"Código {code_idx + 1}: {code_item['codigo']}", expanded=False):
            with st.form(key=f"edit_code_form_{segment_number}_{code_idx}"):
                edited_quote = st.text_area(
                    "Cita",
                    value=code_item["cita"],
                    height=120,
                )
                edited_label = st.text_input(
                    "Código",
                    value=code_item["codigo"],
                )
                edited_note = st.text_area(
                    "Nota analítica",
                    value=code_item.get("nota", ""),
                    height=100,
                )
                save_code_col, delete_code_col = st.columns(2)
                with save_code_col:
                    save_code = st.form_submit_button("Guardar cambios")
                with delete_code_col:
                    delete_code = st.form_submit_button("Eliminar código")

            if save_code:
                if edited_quote.strip() and edited_label.strip():
                    st.session_state.codes[code_idx] = {
                        **st.session_state.codes[code_idx],
                        "cita": edited_quote.strip(),
                        "codigo": edited_label.strip(),
                        "nota": edited_note.strip(),
                    }
                    save_project_state()
                    st.rerun()
                st.warning("La cita y el código son obligatorios.")

            if delete_code:
                st.session_state.codes.pop(code_idx)
                save_project_state()
                st.rerun()


def save_as_docx(text, title, event_date, transcription_date, memos_df, codes_df):
    """Genera un archivo .docx con metadatos, cuerpo, memos y códigos."""
    doc = Document()
    doc.add_heading("Transcripción de Investigación", 0)

    meta_paragraph = doc.add_paragraph()
    meta_paragraph.add_run("Título: ").bold = True
    meta_paragraph.add_run(f"{title}\n")
    meta_paragraph.add_run("Fecha del evento: ").bold = True
    meta_paragraph.add_run(f"{event_date}\n")
    meta_paragraph.add_run("Fecha de transcripción: ").bold = True
    meta_paragraph.add_run(f"{transcription_date}\n")

    doc.add_paragraph("-" * 30)
    add_formatted_transcript(doc, text)

    if not memos_df.empty:
        doc.add_page_break()
        doc.add_heading("Notas de Investigación (Memos)", level=1)
        for _, row in memos_df.iterrows():
            paragraph = doc.add_paragraph()
            paragraph.add_run(f"Segmento {row['segmento']}: ").bold = True
            paragraph.add_run(str(row["memo"]))

    if not codes_df.empty:
        doc.add_page_break()
        doc.add_heading("Codificación", level=1)
        for _, row in codes_df.iterrows():
            paragraph = doc.add_paragraph()
            paragraph.add_run(f"Segmento {row['segmento']} | Código: ").bold = True
            paragraph.add_run(f"{row['codigo']}\n")
            paragraph.add_run("Cita: ").bold = True
            paragraph.add_run(f"{row['cita']}\n")
            if str(row.get("nota", "")).strip():
                paragraph.add_run("Nota: ").bold = True
                paragraph.add_run(f"{row['nota']}\n")

    doc.add_paragraph("\n")
    footer = doc.add_paragraph()
    footer.alignment = 1
    footer_run = footer.add_run(
        "Transcripción hecha con una versión piloto integrada de AudioScript Contextual. "
        "Desarrollado por Teresa Márquez. Departamento de Ciencias Sociales."
    )
    footer_run.font.size = Pt(8)
    footer_run.italic = True

    temp_docx = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".docx",
        dir=TEMP_DIR,
    )
    doc.save(temp_docx.name)
    return temp_docx.name


def render_downloads(text, title, event_date, transcription_date, memos_df=None, codes_df=None):
    """Renderiza botones de descarga para texto, docx, memos y códigos."""
    if memos_df is None:
        memos_df = pd.DataFrame(st.session_state.memos)
    if codes_df is None:
        codes_df = build_codes_dataframe()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            "Descargar .TXT",
            data=text,
            file_name=f"{title}.txt",
            mime="text/plain",
        )
    with col2:
        doc_path = save_as_docx(text, title, event_date, transcription_date, memos_df, codes_df)
        with open(doc_path, "rb") as doc_file:
            st.download_button(
                "Descargar .DOCX",
                data=doc_file.read(),
                file_name=f"{title}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    with col3:
        if memos_df.empty:
            st.button("No hay memos para exportar", disabled=True)
        else:
            csv_data = memos_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar Memos (CSV)",
                data=csv_data,
                file_name=f"{title}_memos.csv",
                mime="text/csv",
            )
    with col4:
        if codes_df.empty:
            st.button("No hay códigos para exportar", disabled=True)
        else:
            csv_data = codes_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar Códigos (CSV)",
                data=csv_data,
                file_name=f"{title}_codigos.csv",
                mime="text/csv",
            )


def main():
    init_session_state()

    render_app_header()

    if not check_ffmpeg():
        st.error("Error: ffmpeg no está instalado. Instálalo con `brew install ffmpeg`.")
        st.stop()

    with st.sidebar:
        st.markdown("## Gestión de Proyecto")

        uploaded_file = st.file_uploader(
            "Subir audio o video",
            type=["mp3", "m4a", "wav", "mp4"],
        )

        if uploaded_file:
            restore_project_if_available(uploaded_file)
            st.success(f"Archivo cargado: {uploaded_file.name}")
            st.markdown(
                f"""
                <div class="project-card">
                  <strong>{st.session_state.main_doc_title or uploaded_file.name}</strong>
                  <span>{st.session_state.main_event_date.strftime("%d/%m/%Y")} · {len(st.session_state.transcript_segments)} segmentos confirmados</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown("## Configuración Rápida")
        mode = st.radio(
            "Modo de procesamiento",
            [
                "Segmentado (Recomendación para transcripciones cualitativas)",
                "Completo (Solo audios cortos)",
            ],
            key="sidebar_mode",
        )
        trans_type = st.radio(
            "Formato de transcripción",
            ["Limpia (Sin muletillas)", "Verbatim (Literal - incluye errores)"],
            key="sidebar_trans_type",
        )

        with st.expander("Ajustes avanzados", expanded=False):
            st.session_state.sidebar_model_choice = select_dial_option(
                "Modelo de transcripción",
                st.session_state.sidebar_model_choice,
                ["tiny", "base", "small", "medium", "large"],
                "model_dial",
            )
            model_choice = st.session_state.sidebar_model_choice
            language_choice = st.selectbox(
                "Idioma",
                ["Detección automática", "Español", "Inglés"],
                key="sidebar_language_choice",
            )
            editor_font_size = render_font_size_dial()
            if "Segmentado" in mode:
                st.number_input(
                    "Minutos por segmento",
                    min_value=1,
                    max_value=30,
                    key="sidebar_segment_mins",
                )

        st.markdown("## Estado")
        render_sidebar_circle(
            "Tiempo",
            f"{st.session_state.sidebar_segment_mins} min" if "Segmentado" in mode else "Completo",
        )
        render_sidebar_circle(
            "Conexión",
            "Offline",
            "Estás trabajando en local, tus datos están protegidos.",
        )

        with st.expander("Ayuda y guía", expanded=False):
            st.markdown(
                """
                1. Sube un audio o video.
                2. Completa metadatos y términos clave en la zona principal.
                3. Usa modo completo para audios cortos o segmentado para revisión detallada.
                4. Agrega memos durante la revisión segmentada.
                5. Exporta la transcripción final en TXT, DOCX y los memos en CSV.
                """
            )

        st.divider()
        if st.button("Limpiar todo"):
            delete_project_state(st.session_state.current_project_id)
            reset_transcription_state()
            st.session_state.current_project_id = None
            st.session_state.uploaded_file_id = None
            st.session_state.autosave_last_saved = ""
            st.rerun()

    if not uploaded_file:
        st.info("Esperando archivo... Por favor sube un audio o video desde el menú lateral.")
        return

    apply_editor_styles(editor_font_size)

    temp_audio_path = get_project_audio_path(
        st.session_state.current_project_id,
        uploaded_file.name,
    )
    ensure_project_chunks(temp_audio_path)
    memos_df = pd.DataFrame(st.session_state.memos)
    codes_df = build_codes_dataframe()

    with st.expander("Metadatos y contexto de la transcripción", expanded=True):
        meta_col, context_col = st.columns([1, 1.2])
        with meta_col:
            st.text_input(
                "Título de la transcripción",
                key="main_doc_title",
            )
            st.date_input("Fecha del evento", key="main_event_date")
            st.text_input(
                "Fecha de transcripción",
                key="main_transcription_date",
                disabled=True,
            )
        with context_col:
            st.text_area(
                "Nombres y términos técnicos",
                placeholder="Ej: Juan Pérez, fenomenología, ATLAS.ti...",
                height=140,
                key="main_custom_terms",
            )

    doc_title = st.session_state.main_doc_title
    event_date = st.session_state.main_event_date.strftime("%d/%m/%Y")
    transcription_date = st.session_state.main_transcription_date
    custom_terms = st.session_state.main_custom_terms
    segment_mins = st.session_state.sidebar_segment_mins

    st.caption(
        f"Guardado automático activo. Último guardado: {st.session_state.autosave_last_saved or 'pendiente'}"
    )

    if mode == "Completo (Solo audios cortos)":
        workspace_col, side_col = st.columns([3.6, 1.4], gap="large")
        render_keyboard_shortcuts(False)
        with workspace_col:
            open_card("Transcripción Completa")
            if st.button("Iniciar Transcripción Completa"):
                with st.spinner("Transcribiendo audio completo..."):
                    try:
                        text = transcribe_audio(
                            temp_audio_path,
                            model_choice,
                            language_choice,
                            custom_terms,
                            trans_type,
                        )
                        st.session_state.last_transcription = text
                        save_project_state()
                    except Exception as exc:
                        st.error(f"Error durante la transcripción: {exc}")

            if st.session_state.last_transcription:
                toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([1.4, 1.4, 1])
                with toolbar_col1:
                    complete_find_term = st.text_input(
                        "Buscar en transcripción",
                        key="complete_find_term",
                    )
                with toolbar_col2:
                    complete_replace_term = st.text_input(
                        "Reemplazar con",
                        key="complete_replace_term",
                    )
                with toolbar_col3:
                    if st.button("Reemplazar", key="complete_replace_btn"):
                        if complete_find_term:
                            st.session_state.last_transcription = (
                                st.session_state.last_transcription.replace(
                                    complete_find_term,
                                    complete_replace_term,
                                )
                            )
                            save_project_state()
                            st.rerun()

                final_text = st.text_area(
                    "Edite el texto si es necesario",
                    value=st.session_state.last_transcription,
                    height=420,
                )
                st.session_state.last_transcription = final_text
                render_selectable_transcript_panel(
                    final_text,
                    highlight_term=complete_find_term,
                )
                render_downloads(
                    final_text,
                    doc_title,
                    event_date,
                    transcription_date,
                )
            else:
                st.info("Cuando inicies la transcripción completa, el texto aparecerá aquí.")
            close_card()

        with side_col:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            render_memo_manager(0)
            close_card()
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            render_code_manager(0)
            close_card()
        save_project_state()
        st.markdown(
            '<div class="footer-bar">UNIVERSIDAD IBEROAMERICANA 2026 &nbsp; | &nbsp; Ciencias Sociales y Políticas</div>',
            unsafe_allow_html=True,
        )
        return

    if not st.session_state.chunks:
        if st.button("Dividir audio en segmentos"):
            with st.spinner("Dividiendo audio..."):
                try:
                    st.session_state.chunks = split_audio(
                        temp_audio_path,
                        segment_mins,
                        get_project_chunks_dir(st.session_state.current_project_id),
                    )
                    st.session_state.chunks_prepared = True
                    st.session_state.chunk_segment_mins = segment_mins
                    st.session_state.current_chunk_idx = 0
                    save_project_state()
                    st.success(
                        f"Audio dividido en {len(st.session_state.chunks)} segmentos."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error al dividir el audio: {exc}")

    chunks = st.session_state.chunks
    idx = st.session_state.current_chunk_idx

    if not chunks:
        st.info("Haz clic en 'Dividir audio en segmentos' para comenzar.")
        save_project_state()
        return

    if idx < len(chunks):
        pending_segment_action = st.session_state.get("pending_segment_action")
        if pending_segment_action == "advance":
            if st.session_state.current_segment_text.strip():
                st.session_state.transcript_segments.append(
                    st.session_state.current_segment_text.strip()
                )
                st.session_state.current_chunk_idx += 1
                st.session_state.current_segment_text = ""
            st.session_state.pending_segment_action = None
            save_project_state()
            chunks = st.session_state.chunks
            idx = st.session_state.current_chunk_idx
            if idx >= len(chunks):
                st.rerun()
        elif pending_segment_action == "reset":
            st.session_state.current_segment_text = ""
            st.session_state.pending_segment_action = None
            save_project_state()

        st.markdown(f"### Segmento {idx + 1} de {len(chunks)}")
        st.progress(idx / len(chunks))
        if (
            st.session_state.chunk_segment_mins
            and st.session_state.chunk_segment_mins != segment_mins
        ):
            st.info(
                "Cambiaste los minutos por segmento. Para aplicar ese cambio, vuelve a dividir el audio."
            )
        render_keyboard_shortcuts(True)

        col_main, col_side = st.columns([3.6, 1.4], gap="large")

        with col_main:
            open_card("Control de Reproducción")
            render_segment_audio_player(chunks[idx])
            st.caption(
                "Atajos: `Ctrl+Shift+T` transcribe, `Ctrl+Enter` confirma, `Ctrl+Shift+R` reinicia, `Alt + ←/→` mueve el audio."
            )
            close_card()

            open_card("Transcripción")
            toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([1.3, 1.3, 1, 1])
            with toolbar_col1:
                find_term = st.text_input("Buscar en transcripción", key=f"find_term_{idx}")
            with toolbar_col2:
                replace_term = st.text_input("Reemplazar con", key=f"replace_term_{idx}")
            with toolbar_col3:
                if st.button("Reemplazar", key=f"replace_btn_{idx}"):
                    if find_term:
                        st.session_state.current_segment_text = (
                            st.session_state.current_segment_text.replace(find_term, replace_term)
                        )
                        save_project_state()
                        st.rerun()
            with toolbar_col4:
                if st.button("Transcribir", key=f"transcribe_btn_{idx}"):
                    with st.spinner("Whisper está transcribiendo..."):
                        try:
                            text = transcribe_audio(
                                chunks[idx],
                                model_choice,
                                language_choice,
                                custom_terms,
                                trans_type,
                            )
                            st.session_state.current_segment_text = text
                            save_project_state()
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error en transcripción: {exc}")

            if find_term:
                occurrences = st.session_state.current_segment_text.lower().count(find_term.lower())
                st.caption(f"Coincidencias encontradas en el fragmento: {occurrences}")

            render_selectable_transcript_panel(
                st.session_state.current_segment_text,
                highlight_term=find_term,
            )
            st.caption("Selecciona con el mouse una frase del panel superior y pulsa `Codificar selección`.")

            st.text_area(
                "Edite este fragmento antes de continuar",
                height=280,
                key="current_segment_text",
            )

            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1:
                if st.button("Confirmar y Siguiente"):
                    if st.session_state.current_segment_text.strip():
                        st.session_state.pending_segment_action = "advance"
                        st.rerun()
                    st.warning("No hay texto para guardar.")
            with c2:
                if st.button("Reiniciar segmento"):
                    st.session_state.pending_segment_action = "reset"
                    st.rerun()
            with c3:
                st.button("Segmentación activa", disabled=True)
            with c4:
                st.metric("Palabras", len(st.session_state.current_segment_text.split()))

            stats = [
                ("Segmentos", str(len(st.session_state.transcript_segments))),
                ("Memos", str(len(st.session_state.memos))),
                ("Códigos", str(len(st.session_state.codes))),
                ("Caracteres", str(len(st.session_state.current_segment_text))),
            ]
            st.markdown(
                '<div class="mini-stat-grid">' +
                "".join(
                    [
                        f'<div class="mini-stat"><div class="mini-stat__label">{label}</div><div class="mini-stat__value">{value}</div></div>'
                        for label, value in stats
                    ]
                ) +
                '</div>',
                unsafe_allow_html=True,
            )
            close_card()

        with col_side:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            with st.container():
                render_memo_manager(idx + 1)
            close_card()

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            with st.container():
                render_code_manager(idx + 1)
            close_card()
        save_project_state()
        st.markdown(
            '<div class="footer-bar">UNIVERSIDAD IBEROAMERICANA 2026 &nbsp; | &nbsp; Ciencias Sociales y Políticas</div>',
            unsafe_allow_html=True,
        )
        return

    st.success("Transcripción completada")
    workspace_col, side_col = st.columns([3.6, 1.4], gap="large")
    full_text = "\n\n".join(st.session_state.transcript_segments)
    render_keyboard_shortcuts(True)
    with workspace_col:
        open_card("Transcripción Consolidada")
        toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([1.4, 1.4, 1])
        with toolbar_col1:
            final_find_term = st.text_input(
                "Buscar en transcripción",
                key="final_find_term",
            )
        with toolbar_col2:
            final_replace_term = st.text_input(
                "Reemplazar con",
                key="final_replace_term",
            )
        with toolbar_col3:
            if st.button("Reemplazar", key="final_replace_btn"):
                if final_find_term:
                    updated_segments = [
                        segment.replace(final_find_term, final_replace_term)
                        for segment in st.session_state.transcript_segments
                    ]
                    st.session_state.transcript_segments = updated_segments
                    save_project_state()
                    st.rerun()

        final_view = st.text_area(
            "Contenido consolidado",
            value=full_text,
            height=420,
        )
        render_selectable_transcript_panel(
            final_view,
            highlight_term=final_find_term,
        )
        render_downloads(
            final_view,
            doc_title,
            event_date,
            transcription_date,
        )

        if st.button("Empezar de nuevo"):
            delete_project_state(st.session_state.current_project_id)
            reset_transcription_state()
            st.session_state.current_project_id = None
            st.session_state.uploaded_file_id = None
            st.session_state.autosave_last_saved = ""
            st.rerun()
        close_card()

    with side_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_memo_manager(0)
        close_card()
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_code_manager(0)
        close_card()

    save_project_state()
    st.markdown(
        '<div class="footer-bar">UNIVERSIDAD IBEROAMERICANA 2026 &nbsp; | &nbsp; Ciencias Sociales y Políticas</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
