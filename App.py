import os
import re
import json
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
    st.session_state.memos = []
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

        speaker_match = re.match(r"^([A-Za-zÁÉÍÓÚáéíóúÑñ\s]+:)\s*(.*)$", line)
        if speaker_match:
            paragraph = doc.add_paragraph()
            speaker_label, spoken_text = speaker_match.groups()
            paragraph.add_run(speaker_label).bold = True
            if spoken_text:
                paragraph.add_run(f" {spoken_text}")
        else:
            doc.add_paragraph(line)


def save_as_docx(text, title, event_date, transcription_date, memos_df):
    """Genera un archivo .docx con metadatos, cuerpo y memos."""
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


def render_downloads(text, title, event_date, transcription_date, memos_df):
    """Renderiza botones de descarga para texto, docx y memos."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Descargar .TXT",
            data=text,
            file_name=f"{title}.txt",
            mime="text/plain",
        )
    with col2:
        doc_path = save_as_docx(text, title, event_date, transcription_date, memos_df)
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


def main():
    init_session_state()

    st.markdown(
        '<h3 class="main-title">Audioscript Contextual Pro. Transcripción inmersiva potenciada por IA en local</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-title">Versión fusionada para investigación cualitativa. Por Teresa Márquez</p>',
        unsafe_allow_html=True,
    )

    if not check_ffmpeg():
        st.error("Error: ffmpeg no está instalado. Instálalo con `brew install ffmpeg`.")
        st.stop()

    with st.sidebar:
        st.title("Control rápido")

        uploaded_file = st.file_uploader(
            "Subir audio o video",
            type=["mp3", "m4a", "wav", "mp4"],
        )

        if uploaded_file:
            restore_project_if_available(uploaded_file)
            st.success(f"Archivo cargado: {uploaded_file.name}")

        st.divider()
        mode = st.radio(
            "Modo de procesamiento",
            [
                "Segmentado (Recomendación para transcripciones cualitativas)",
                "Completo (Solo audios cortos)",
            ],
            key="sidebar_mode",
        )

        with st.expander("Ajustes avanzados", expanded=False):
            model_choice = st.selectbox(
                "Modelo de Whisper",
                ["tiny", "base", "small", "medium", "large"],
                key="sidebar_model_choice",
            )
            language_choice = st.selectbox(
                "Idioma",
                ["Detección automática", "Español", "Inglés"],
                key="sidebar_language_choice",
            )
            trans_type = st.radio(
                "Formato de transcripción",
                ["Limpia (Sin muletillas)", "Verbatim (Literal - incluye errores)"],
                key="sidebar_trans_type",
            )
            if "Segmentado" in mode:
                st.number_input(
                    "Minutos por segmento",
                    min_value=1,
                    max_value=30,
                    key="sidebar_segment_mins",
                )
            editor_font_size = st.slider(
                "Tamaño de letra del editor",
                min_value=12,
                max_value=28,
                step=1,
                key="sidebar_editor_font_size",
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
        render_keyboard_shortcuts(False)
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
            st.subheader("Revisión de transcripción")
            final_text = st.text_area(
                "Edite el texto si es necesario",
                value=st.session_state.last_transcription,
                height=420,
            )
            st.session_state.last_transcription = final_text
            render_downloads(
                final_text,
                doc_title,
                event_date,
                transcription_date,
                memos_df,
            )
        save_project_state()
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
        st.subheader(f"Segmento {idx + 1} de {len(chunks)}")
        st.progress(idx / len(chunks))
        if (
            st.session_state.chunk_segment_mins
            and st.session_state.chunk_segment_mins != segment_mins
        ):
            st.info(
                "Cambiaste los minutos por segmento. Para aplicar ese cambio, vuelve a dividir el audio."
            )
        render_keyboard_shortcuts(True)

        col_main, col_memo = st.columns([1.3, 1])

        with col_main:
            st.markdown("### Reproductor del segmento")
            render_segment_audio_player(chunks[idx])
            st.caption(
                "Atajos: `Ctrl+Shift+T` transcribe, `Ctrl+Enter` confirma, `Ctrl+Shift+R` reinicia."
            )

            if st.button("Transcribir este fragmento"):
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

            st.text_area(
                "Edite este fragmento antes de continuar",
                height=340,
                key="current_segment_text",
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Confirmar y Siguiente"):
                    if st.session_state.current_segment_text.strip():
                        st.session_state.transcript_segments.append(
                            st.session_state.current_segment_text.strip()
                        )
                        st.session_state.current_chunk_idx += 1
                        st.session_state.current_segment_text = ""
                        save_project_state()
                        st.rerun()
                    st.warning("No hay texto para guardar.")
            with c2:
                if st.button("Reiniciar segmento"):
                    st.session_state.current_segment_text = ""
                    save_project_state()
                    st.rerun()
            with c3:
                st.button("Segmentación activa", disabled=True)

        with col_memo:
            st.markdown("### Memos de análisis")
            st.caption("Anotaciones rápidas para complementar la transcripción.")

            memo_input = st.text_area(
                "Nueva anotación",
                key=f"memo_input_{idx}",
                height=140,
            )
            if st.button("Guardar Memo"):
                if memo_input.strip():
                    st.session_state.memos.append(
                        {"segmento": idx + 1, "memo": memo_input.strip()}
                    )
                    st.session_state[f"memo_input_{idx}"] = ""
                    save_project_state()
                    st.rerun()
                st.warning("Escribe un memo antes de guardarlo.")

            st.markdown("---")
            if st.session_state.memos:
                for memo in st.session_state.memos:
                    st.info(f"Seg {memo['segmento']}: {memo['memo']}")
            else:
                st.write("Todavía no hay memos.")
        save_project_state()
        return

    st.success("Transcripción completada")
    full_text = "\n\n".join(st.session_state.transcript_segments)
    render_keyboard_shortcuts(True)
    final_view = st.text_area(
        "Contenido consolidado",
        value=full_text,
        height=420,
    )
    render_downloads(
        final_view,
        doc_title,
        event_date,
        transcription_date,
        pd.DataFrame(st.session_state.memos),
    )

    if st.button("Empezar de nuevo"):
        delete_project_state(st.session_state.current_project_id)
        reset_transcription_state()
        st.session_state.current_project_id = None
        st.session_state.uploaded_file_id = None
        st.session_state.autosave_last_saved = ""
        st.rerun()

    save_project_state()


if __name__ == "__main__":
    main()
