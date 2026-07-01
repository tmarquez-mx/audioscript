import base64
import html
import json
import os
import re
import textwrap
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


def render_dom_html(body, *, width="stretch", allow_js=False):
    """Renderiza HTML inline usando la API moderna de Streamlit."""
    st.html(body, width=width, unsafe_allow_javascript=allow_js)


def render_dom_script(script_body):
    """Inyecta scripts sin dejar contenedores visibles en la UI."""
    render_dom_html(
        f"<script>{script_body}</script><div style='display:none'></div>",
        allow_js=True,
    )


def apply_editor_styles(font_size_px, reading_mode=False):
    """Ajusta el tamano y estilo de las areas principales de transcripcion."""
    reading_font_size = 19
    line_height = 1.5 if reading_mode else 1.6
    text_color = "#4e5a67" if reading_mode else "#2b3443"
    background_color = "#f5efe3" if reading_mode else "#fffdf8"
    border_color = "rgba(145, 117, 67, 0.22)" if reading_mode else "rgba(37,42,50,.13)"
    font_family = (
        "Georgia, 'Iowan Old Style', serif"
        if reading_mode
        else "'Inter', 'Roboto', sans-serif"
    )
    width_rule = "width: 100% !important; max-width: none !important;" if reading_mode else ""
    container_rule = "width: 100%; max-width: 100%; margin: 0;" if reading_mode else "max-width: 100%;"
    horizontal_padding = (
        "max(18%, calc((100% - 39rem) / 2))"
        if reading_mode
        else "1.25rem"
    )
    vertical_padding = "1.6rem" if reading_mode else "1.15rem"
    mobile_reading_rule = (
        """
        @media (max-width: 700px) {
          textarea[aria-label="Edite este fragmento antes de continuar"],
          textarea[aria-label="Edite el texto si es necesario"],
          textarea[aria-label="Contenido consolidado"] {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
          }
        }
        """
        if reading_mode
        else ""
    )
    st.markdown(
        f"""
        <style>
        div[data-testid="stTextArea"]:has(textarea[aria-label="Edite este fragmento antes de continuar"]),
        div[data-testid="stTextArea"]:has(textarea[aria-label="Edite el texto si es necesario"]),
        div[data-testid="stTextArea"]:has(textarea[aria-label="Contenido consolidado"]) {{
            {container_rule}
        }}
        textarea[aria-label="Edite este fragmento antes de continuar"],
        textarea[aria-label="Edite el texto si es necesario"],
        textarea[aria-label="Contenido consolidado"] {{
            font-size: {reading_font_size if reading_mode else font_size_px}px !important;
            line-height: {line_height} !important;
            font-family: {font_family} !important;
            color: {text_color} !important;
            background: {background_color} !important;
            border: 1px solid {border_color} !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.55) !important;
            letter-spacing: 0.01em !important;
            box-sizing: border-box !important;
            padding-top: {vertical_padding} !important;
            padding-bottom: {vertical_padding} !important;
            padding-left: {horizontal_padding} !important;
            padding-right: {horizontal_padding} !important;
            {width_rule}
        }}
        {mobile_reading_rule}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_app_header():
    """Dibuja la cabecera identitaria de AudioScript Contextual."""
    st.markdown(
        """
        <header class="audioscript-identity-header">
          <div class="audioscript-identity-brand">
            <svg class="audioscript-identity-mark" viewBox="0 0 120 56" role="img"
                 aria-label="AudioScript Contextual: onda de audio y escritura sobre una misma línea">
              <line x1="7" y1="40" x2="110" y2="40" stroke="rgba(255,255,255,.22)"
                    stroke-width="2" stroke-linecap="round"></line>
              <rect x="7.5" y="22" width="5" height="18" rx="2.5" fill="#86abce"></rect>
              <rect x="16.5" y="8" width="5" height="32" rx="2.5" fill="#86abce"></rect>
              <rect x="25.5" y="16" width="5" height="24" rx="2.5" fill="#86abce"></rect>
              <rect x="34.5" y="2" width="5" height="38" rx="2.5" fill="#a9c4e0"></rect>
              <rect x="43.5" y="24" width="5" height="16" rx="2.5" fill="#86abce"></rect>
              <path d="M55 40 q 5 -15 11 -3 q 4 9 9 1 q 5 -11 10 0 q 4 8 9 -2"
                    fill="none" stroke="#d98a5a" stroke-width="4.5"
                    stroke-linecap="round" stroke-linejoin="round"></path>
              <circle cx="100" cy="40" r="2.8" fill="#d98a5a"></circle>
            </svg>
            <div class="audioscript-identity-copy">
              <div class="audioscript-identity-name">
                <span class="audioscript-identity-name-a">AudioScript</span>
                <span class="audioscript-identity-name-c">Contextual</span>
              </div>
              <div class="audioscript-identity-tagline">
                Transcripción inmersiva potenciada por IA
                <em>y pensada desde el oficio cualitativo</em>
              </div>
            </div>
          </div>
          <div class="audioscript-identity-lema" aria-label="Lema de AudioScript Contextual">
            <span>Tu ritmo</span>
            <span>Tu profundidad</span>
            <span>Tu soberanía</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )

def render_ai_margin_panel(segment_number, text):
    """Panel derecho de apoyo analítico local."""
    words = re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑ]{5,}\b", text or "", re.UNICODE)
    stopwords = {
        "entonces", "porque", "cuando", "también", "sobre", "desde", "hasta",
        "puede", "pueden", "tiene", "tienen", "forma", "mismo", "misma",
        "transcripción", "segmento", "contexto",
    }
    counts = {}
    for word in words:
        normalized = word.lower()
        if normalized not in stopwords:
            counts[normalized] = counts.get(normalized, 0) + 1
    keywords = sorted(counts, key=counts.get, reverse=True)[:4] or [
        "ritmo",
        "contexto",
        "experiencia",
    ]
    summary = (
        "Este margen resume señales de lectura cuando hay texto transcrito. "
        "Usa las sugerencias como punto de partida, no como interpretación final."
    )
    if text.strip():
        summary = (
            f"Segmento {segment_number}: {len(text.split())} palabras. "
            "Revisa hablantes, frases con densidad analítica y posibles códigos emergentes."
        )

    st.markdown(
        f"""
        <div class="section-card section-card--ai">
          <div class="section-title">Memos y análisis IA</div>
          <div class="ai-card ai-card--featured">
            <div class="ai-margin-title">Resumen contextual</div>
            <p>{html.escape(summary)}</p>
          </div>
          <div class="ai-card">
            <div class="ai-margin-title">Códigos sugeridos</div>
            {''.join([f'<span class="ai-chip">{html.escape(keyword)}</span>' for keyword in keywords])}
          </div>
          <div class="ai-card">
            <div class="ai-margin-title">Próxima lectura</div>
            <p>Selecciona una frase del documento central para codificarla o convertirla en memo analítico.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_audio_console_header(segment_label):
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:.65rem;">
          <div>
            <div class="transcript-toolbar-label">Control de reproducción</div>
            <strong>{html.escape(segment_label)}</strong>
          </div>
          <div class="ai-chip">Audio local</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_transcript_toolbar_title(title):
    st.markdown(
        f"""
        <div style="margin-bottom:.75rem;">
          <div class="transcript-toolbar-label">Documento de trabajo</div>
          <div class="section-title" style="margin-bottom:0;">{html.escape(title)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_transcript_panel_label(title, description):
    """Etiqueta los paneles de texto para distinguir lectura y edición."""
    st.markdown(
        f"""
        <div style="margin:.9rem 0 .35rem 0;">
          <div class="transcript-toolbar-label">{html.escape(title)}</div>
          <div style="color:#5d6876;font-size:.88rem;line-height:1.35;">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

DIFFERENTIATOR_ICON_DIR = Path(__file__).parent / "assets" / "differentiator-icons"
DIFFERENTIATOR_WATERMARKS = (
    ("local-data-sovereignty.svg", "Soberanía de datos"),
    ("methodological-control.svg", "Control metodológico"),
    ("offline-fieldwork.svg", "Trabajo sin conexión"),
    ("accessible-cost.svg", "Freeware sin costo"),
)


def render_workspace_watermarks():
    """Muestra una constelacion sutil de iconos en el estado inicial de la mesa central."""
    marks = []
    for filename, label in DIFFERENTIATOR_WATERMARKS:
        svg_path = DIFFERENTIATOR_ICON_DIR / filename
        if not svg_path.exists():
            continue
        svg_data = base64.b64encode(svg_path.read_bytes()).decode("ascii")
        marks.append(
            '<div class="workspace-watermark__mark">'
            '<div class="workspace-watermark__icon">'
            f'<img src="data:image/svg+xml;base64,{svg_data}" alt="" aria-hidden="true">'
            '</div>'
            f'<div class="workspace-watermark__label">{html.escape(label)}</div>'
            '</div>'
        )

    if not marks:
        return

    markup = (
        '<section class="workspace-watermark">'
        '<div class="workspace-watermark__grid">'
        f'{"".join(marks)}'
        '</div>'
        '</section>'
    )
    st.markdown(markup, unsafe_allow_html=True)


def compact_html_fragment(fragment):
    """Elimina indentacion multilinea para evitar que Streamlit la interprete como codigo."""
    normalized = textwrap.dedent(fragment).strip()
    normalized = re.sub(r">\s+<", "><", normalized)
    normalized = re.sub(r"\s{2,}", " ", normalized)
    return normalized


def render_beta_installer_preview(step, selected_model="medium"):
    """Simulacion visual del flujo de primera instalacion para beta testers."""
    selected = "large" if str(selected_model).lower() == "large" else "medium"
    selected_label = "Large" if selected == "large" else "Medium"
    download_size = "3 GB" if selected == "large" else "1.5 GB"
    disk_space = "5 a 6 GB libres" if selected == "large" else "3 a 4 GB libres"
    summary_use = (
        "Solo si deseas priorizar precisión sobre velocidad."
        if selected == "large"
        else "Opción principal recomendada para la beta."
    )

    screen_map = {
        1: compact_html_fragment(f"""
            <div class="installer-preview__eyebrow">Pantalla 1 de 5</div>
            <h3 class="installer-preview__title">Instala el motor de transcripción local</h3>
            <p class="installer-preview__lead">
              AudioScript Contextual necesita instalar una sola vez el modelo de Whisper que realizará
              las transcripciones en tu Mac.
            </p>
            <p class="installer-preview__body">
              Después de esta instalación inicial, la app funcionará sin conectarse a servidores y tus audios
              se procesarán localmente.
            </p>
            <ul class="installer-preview__benefits-list">
              <li>Procesamiento local después de la instalación</li>
              <li>Sin suscripciones</li>
              <li>Solo para Mac Apple Silicon</li>
              <li>Requiere internet solo para descargar el modelo</li>
            </ul>
            <div class="installer-preview__footnote">Versión beta para evaluación.</div>
        """),
        2: compact_html_fragment(f"""
            <div class="installer-preview__eyebrow">Pantalla 2 de 5</div>
            <h3 class="installer-preview__title">Elige tu modelo de transcripción</h3>
            <p class="installer-preview__body">
              Puedes empezar con la opción recomendada o elegir una versión más pesada para buscar una mayor
              precisión en audios complejos.
            </p>
            <div class="installer-preview__choices">
              <article class="installer-choice {'installer-choice--selected' if selected == 'medium' else ''}">
                <div class="installer-choice__header">
                  <strong>Medium</strong>
                  <span class="installer-choice__badge">Recomendado</span>
                </div>
                <p>Buen equilibrio entre precisión, velocidad y tamaño. Recomendado para entrevistas, grupos focales, clases y trabajo cualitativo cotidiano.</p>
                <ul>
                  <li>Descarga aproximada: 1.5 GB</li>
                  <li>Espacio recomendado: 3 a 4 GB libres</li>
                  <li>Uso sugerido: opción principal para la beta</li>
                </ul>
                <div class="installer-choice__note">Opción recomendada para la beta</div>
              </article>
              <article class="installer-choice {'installer-choice--selected' if selected == 'large' else ''}">
                <div class="installer-choice__header">
                  <strong>Large</strong>
                </div>
                <p>Mayor precisión potencial en audios difíciles, con más matices o condiciones acústicas menos favorables. Requiere más espacio y más tiempo.</p>
                <ul>
                  <li>Descarga aproximada: 3 GB</li>
                  <li>Espacio recomendado: 5 a 6 GB libres</li>
                  <li>Uso sugerido: solo si deseas priorizar precisión sobre velocidad</li>
                </ul>
                <div class="installer-choice__note installer-choice__note--secondary">Opción avanzada de mayor precisión</div>
              </article>
            </div>
            <div class="installer-preview__footnote">Podrás cambiar de modelo más adelante.</div>
        """),
        3: compact_html_fragment(f"""
            <div class="installer-preview__eyebrow">Pantalla 3 de 5</div>
            <h3 class="installer-preview__title">Antes de instalar</h3>
            <div class="installer-preview__summary">
              <div><span>Modelo seleccionado</span><strong>{selected_label}</strong></div>
              <div><span>Conexión requerida</span><strong>Solo para esta descarga</strong></div>
              <div><span>Procesamiento posterior</span><strong>Local y sin conexión</strong></div>
              <div><span>Ubicación de instalación</span><strong>Library/Application Support/AudioScript Contextual</strong></div>
            </div>
            <p class="installer-preview__body">
              AudioScript descargará el modelo seleccionado y lo guardará en tu Mac para reutilizarlo sin volver
              a conectarse. Tus audios no se enviarán a servidores.
            </p>
            <div class="installer-preview__warning">
              <strong>Aviso sobre esta beta</strong>
              <p>Esta versión de AudioScript Contextual aún no está firmada ni notarizada por Apple.</p>
              <p>Por ello, macOS puede mostrar advertencias de seguridad al abrirla por primera vez.</p>
              <p>Si eso ocurre, podrás continuar manualmente desde Configuración del Sistema &gt; Privacidad y seguridad &gt; Abrir de todos modos.</p>
              <p>Se trata de una beta de evaluación distribuida de forma controlada.</p>
            </div>
        """),
        4: compact_html_fragment(f"""
            <div class="installer-preview__eyebrow">Pantalla 4 de 5</div>
            <h3 class="installer-preview__title">Instalando modelo de transcripción</h3>
            <p class="installer-preview__lead">AudioScript está preparando tu motor de transcripción local.</p>
            <div class="installer-preview__progress">
              <div class="installer-preview__progress-fill"></div>
            </div>
            <div class="installer-preview__status-list">
              <span class="is-active">Descargando modelo {selected_label}...</span>
              <span>Verificando archivo...</span>
              <span>Preparando uso local...</span>
              <span>Finalizando instalación...</span>
            </div>
            <div class="installer-preview__meta-grid">
              <div><span>Descarga estimada</span><strong>{download_size}</strong></div>
              <div><span>Espacio recomendado</span><strong>{disk_space}</strong></div>
              <div><span>Uso sugerido</span><strong>{summary_use}</strong></div>
            </div>
            <div class="installer-preview__soft-note">
              Este proceso puede tardar varios minutos según tu conexión. No cierres la aplicación.
            </div>
        """),
        5: compact_html_fragment(f"""
            <div class="installer-preview__eyebrow">Pantalla 5 de 5</div>
            <h3 class="installer-preview__title">AudioScript está listo</h3>
            <p class="installer-preview__lead">El modelo quedó instalado correctamente en tu Mac.</p>
            <p class="installer-preview__body">
              A partir de ahora, tus transcripciones se realizarán localmente, sin enviar audios a servidores.
            </p>
            <div class="installer-preview__ready-grid">
              <div><span>Modelo instalado</span><strong>{selected_label}</strong></div>
              <div><span>Estado</span><strong>Listo para uso offline</strong></div>
              <div><span>Privacidad</span><strong>Procesamiento local</strong></div>
            </div>
        """),
    }

    rail_markup = "".join(
        f'<span class="installer-preview__dot {"is-current" if dot_step == step else ""}"></span>'
        for dot_step in range(1, 6)
    )
    body_markup = (
        '<section class="installer-preview">'
        f'<div class="installer-preview__rail">{rail_markup}</div>'
        f'<div class="installer-preview__card">{screen_map.get(step, screen_map[1])}</div>'
        '</section>'
    )
    render_dom_html(
        f"""
          <style>
            html, body {{
              margin: 0;
              padding: 0;
              background: transparent;
              font-family: "Inter", "Roboto", sans-serif;
              color: #2b3443;
            }}
            .installer-preview {{
              display: grid;
              grid-template-columns: 34px minmax(0, 1fr);
              gap: 0.95rem;
              align-items: stretch;
              margin: 0.35rem 0 0;
            }}
            .installer-preview__rail {{
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              gap: 10px;
              padding: 1rem 0;
            }}
            .installer-preview__dot {{
              width: 10px;
              height: 10px;
              border-radius: 999px;
              background: rgba(18, 57, 95, 0.14);
              box-shadow: 0 0 0 6px rgba(18, 57, 95, 0.05);
            }}
            .installer-preview__dot.is-current {{
              background: #c86d3f;
              box-shadow: 0 0 0 7px rgba(200, 109, 63, 0.14);
            }}
            .installer-preview__card {{
              border: 1px solid rgba(18, 57, 95, 0.12);
              border-left: 6px solid #c86d3f;
              border-radius: 22px;
              background: linear-gradient(180deg, rgba(255,253,247,0.96) 0%, rgba(246,248,251,0.94) 100%);
              box-shadow: 0 22px 40px rgba(20, 46, 83, 0.08);
              padding: 1.35rem 1.45rem 1.2rem;
            }}
            .installer-preview__eyebrow {{
              color: #9a552e;
              font-size: 0.75rem;
              font-weight: 800;
              letter-spacing: 0.16em;
              text-transform: uppercase;
              margin-bottom: 0.45rem;
            }}
            .installer-preview__title {{
              margin: 0;
              color: #12395f;
              font-family: Georgia, "Times New Roman", serif;
              font-size: 1.78rem;
              line-height: 1.1;
            }}
            .installer-preview__lead {{
              margin: 0.95rem 0 0.4rem;
              color: #2b3443;
              font-size: 1.14rem;
              font-weight: 700;
              line-height: 1.58;
            }}
            .installer-preview__body {{
              margin: 0.55rem 0 0;
              color: #617080;
              font-size: 1.05rem;
              line-height: 1.72;
            }}
            .installer-preview__choices,
            .installer-preview__summary,
            .installer-preview__meta-grid,
            .installer-preview__ready-grid,
            .installer-preview__status-list {{
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
              gap: 0.75rem;
              margin-top: 1rem;
            }}
            .installer-preview__benefits-list {{
              margin: 1rem 0 0;
              padding-left: 1.15rem;
              color: #617080;
              font-size: 0.98rem;
              line-height: 1.76;
            }}
            .installer-preview__benefits-list li {{
              margin: 0.12rem 0;
              padding-left: 0.2rem;
            }}
            .installer-preview__status-list span,
            .installer-preview__summary div,
            .installer-preview__meta-grid div,
            .installer-preview__ready-grid div {{
              border-radius: 12px;
              border: 1px solid rgba(18, 57, 95, 0.08);
              background: rgba(255,253,247,0.48);
              padding: 0.68rem 0.78rem;
            }}
            .installer-preview__cta-row {{
              display: flex;
              gap: 0.75rem;
              flex-wrap: wrap;
              margin-top: 1rem;
            }}
            .installer-preview__cta {{
              display: inline-flex;
              align-items: center;
              justify-content: center;
              min-height: 44px;
              padding: 0.72rem 1.1rem;
              border-radius: 999px;
              font-weight: 800;
              letter-spacing: 0.01em;
            }}
            .installer-preview__cta--primary {{
              background: linear-gradient(180deg, #d77b46 0%, #c86d3f 100%);
              color: #fffaf6;
              box-shadow: 0 16px 24px rgba(200, 109, 63, 0.2);
            }}
            .installer-preview__cta--secondary,
            .installer-preview__cta--ghost {{
              background: rgba(255,255,255,0.88);
              color: #12395f;
              border: 1px solid rgba(18, 57, 95, 0.12);
            }}
            .installer-preview__footnote {{
              margin-top: 0.8rem;
              color: #798594;
              font-size: 0.82rem;
            }}
            .installer-choice {{
              border-radius: 18px;
              border: 1px solid rgba(18, 57, 95, 0.11);
              background: rgba(255,255,255,0.84);
              padding: 1rem;
              box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
            }}
            .installer-choice--selected {{
              border-color: rgba(200, 109, 63, 0.34);
              box-shadow: 0 12px 22px rgba(200, 109, 63, 0.12);
            }}
            .installer-choice__header {{
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 0.5rem;
              margin-bottom: 0.6rem;
            }}
            .installer-choice__header strong {{
              color: #12395f;
              font-size: 1.02rem;
            }}
            .installer-choice__badge {{
              border-radius: 999px;
              background: rgba(56, 183, 149, 0.12);
              color: #1e8a71;
              font-size: 0.72rem;
              font-weight: 800;
              padding: 0.3rem 0.55rem;
            }}
            .installer-choice p,
            .installer-preview__warning p,
            .installer-preview__soft-note {{
              color: #617080;
              font-size: 0.9rem;
              line-height: 1.55;
            }}
            .installer-choice ul {{
              margin: 0 0 0.85rem;
              padding-left: 1rem;
              color: #35516c;
              font-size: 0.84rem;
              line-height: 1.5;
            }}
            .installer-choice__note {{
              display: inline-flex;
              align-items: center;
              justify-content: center;
              width: 100%;
              min-height: 40px;
              border-radius: 12px;
              background: rgba(255,250,246,0.78);
              border: 1px dashed rgba(200, 109, 63, 0.24);
              color: #8e5a3d;
              font-size: 0.84rem;
              font-weight: 700;
            }}
            .installer-choice__note--secondary {{
              background: rgba(244, 247, 250, 0.82);
              border-color: rgba(18, 57, 95, 0.16);
              color: #4f6277;
            }}
            .installer-preview__summary span,
            .installer-preview__meta-grid span,
            .installer-preview__ready-grid span {{
              display: block;
              color: #6c7786;
              font-size: 0.74rem;
              font-weight: 700;
              letter-spacing: 0.04em;
              text-transform: uppercase;
              margin-bottom: 0.22rem;
            }}
            .installer-preview__summary strong,
            .installer-preview__meta-grid strong,
            .installer-preview__ready-grid strong {{
              color: #12395f;
              font-size: 0.95rem;
              line-height: 1.35;
            }}
            .installer-preview__warning {{
              margin-top: 0.95rem;
              border-radius: 18px;
              border: 1px solid rgba(200, 109, 63, 0.22);
              background: linear-gradient(180deg, rgba(255,243,234,0.95) 0%, rgba(255,248,242,0.95) 100%);
              padding: 1rem 1.05rem;
            }}
            .installer-preview__warning strong {{
              display: block;
              color: #9a552e;
              margin-bottom: 0.4rem;
              font-size: 1.08rem;
            }}
            .installer-preview__progress {{
              width: 100%;
              height: 14px;
              margin: 1rem 0 0.95rem;
              border-radius: 999px;
              background: rgba(18, 57, 95, 0.08);
              overflow: hidden;
            }}
            .installer-preview__progress-fill {{
              width: 64%;
              height: 100%;
              border-radius: inherit;
              background: linear-gradient(90deg, #d77b46 0%, #38b795 100%);
              box-shadow: 0 0 18px rgba(56, 183, 149, 0.18);
            }}
            .installer-preview__status-list span {{
              color: #617080;
              font-size: 0.92rem;
              font-weight: 700;
              line-height: 1.46;
            }}
            .installer-preview__status-list span.is-active {{
              border-color: rgba(56, 183, 149, 0.22);
              background: rgba(236, 252, 246, 0.92);
              color: #1d7e67;
            }}
            .installer-preview__warning p {{
              font-size: 0.98rem;
              line-height: 1.62;
            }}
            .installer-preview__soft-note {{
              font-size: 0.94rem;
              line-height: 1.6;
            }}
            @media (max-width: 900px) {{
              .installer-preview,
              .installer-preview__benefits,
              .installer-preview__choices,
              .installer-preview__summary,
              .installer-preview__meta-grid,
              .installer-preview__ready-grid,
              .installer-preview__status-list {{
                grid-template-columns: 1fr;
              }}
              .installer-preview {{
                display: block;
              }}
              .installer-preview__rail {{
                flex-direction: row;
                justify-content: flex-start;
                padding-bottom: 0.8rem;
              }}
            }}
          </style>
        {body_markup}
        """,
    )


def render_footer_bar():
    st.markdown(
        """
        <div class="footer-bar">
          © 2026 <a href="https://techiholic.netlify.app/" target="_blank">Teresa Márquez</a>.
          Todos los derechos reservados.
          <a href="https://github.com/tmarquez-mx/audioscript" target="_blank">Versión beta distribuible</a>.
          Impulsada por <a href="https://openai.com/es-419/index/whisper/" target="_blank">Whisper de OpenIA</a>.
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_config_separator():
    """Separa visualmente las opciones de configuracion del panel lateral."""
    st.markdown('<div class="config-separator"></div>', unsafe_allow_html=True)

def keep_sidebar_accessible():
    """Muestra un rescate estable del panel lateral sin provocar recargas."""
    render_dom_script(
        """
        function clickSidebarOpener(doc) {
          const selectors = [
            '[data-testid="stSidebarCollapsedControl"] button',
            '[data-testid="collapsedControl"] button',
            '[data-testid="stSidebarCollapsedControl"]',
            '[data-testid="collapsedControl"]',
            'button[aria-label*="Open sidebar" i]',
            'button[aria-label*="Expand sidebar" i]',
            'button[title*="Open sidebar" i]',
            'button[title*="Expand sidebar" i]'
          ];

          for (const selector of selectors) {
            const target = doc.querySelector(selector);
            if (target && typeof target.click === "function") {
              target.click();
              return true;
            }
          }

          const candidates = Array.from(doc.querySelectorAll('button,[role="button"],[data-testid]'));
          const opener = candidates.find((el) => {
            if (el.id === "audioscript-sidebar-rescue") return false;
            const haystack = [
              el.getAttribute("aria-label"),
              el.getAttribute("title"),
              el.getAttribute("data-testid"),
              el.textContent
            ].filter(Boolean).join(" ").toLowerCase();
            return (
              haystack.includes("open sidebar") ||
              haystack.includes("expand sidebar") ||
              haystack.includes("show sidebar") ||
              haystack.includes("collapsedcontrol") ||
              haystack.includes("sidebarcollapsed")
            );
          });
          if (!opener) return false;
          const nestedButton = opener.matches("button") ? opener : opener.querySelector("button");
          const clickable = nestedButton || opener;
          if (clickable && typeof clickable.click === "function") {
            clickable.click();
            return true;
          }
          return false;
        }

        function revealSidebarControl() {
          const doc = document;
          const sidebar = doc.querySelector('[data-testid="stSidebar"]');
          const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;
          const sidebarVisible = Boolean(
            sidebarRect &&
            sidebarRect.width > 140 &&
            sidebarRect.right > 60 &&
            sidebarRect.left < 40 &&
            window.getComputedStyle(sidebar).visibility !== "hidden"
          );

          const controls = doc.querySelectorAll([
            '[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"]',
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="collapsedControl"] button',
            '[data-testid="stSidebarCollapsedControl"] button',
            '[data-testid="stSidebarCollapseButton"] button'
          ].join(','));
          controls.forEach((control) => {
            control.style.display = 'flex';
            control.style.visibility = 'visible';
            control.style.opacity = '1';
            control.style.zIndex = '999999';
          });

          let rescue = doc.getElementById("audioscript-sidebar-rescue");
          if (!rescue) {
            rescue = doc.createElement("button");
            rescue.id = "audioscript-sidebar-rescue";
            rescue.type = "button";
            rescue.innerText = "☰ Panel";
            rescue.setAttribute("aria-label", "Mostrar panel lateral");
            rescue.style.cssText = [
              "position:fixed",
              "left:12px",
              "top:12px",
              "z-index:999999",
              "border:none",
              "border-radius:999px",
              "padding:9px 13px",
              "background:#0f2f53",
              "color:white",
              "font-weight:800",
              "box-shadow:0 10px 24px rgba(15,47,83,.24)",
              "cursor:pointer"
            ].join(";");
            rescue.onclick = function() {
              clickSidebarOpener(doc);
            };
            doc.body.appendChild(rescue);
          }

          doc.documentElement.classList.toggle("audioscript-sidebar-collapsed", !sidebarVisible);
          rescue.style.display = sidebarVisible ? "none" : "inline-flex";
        }
        if (!window.__audioscriptSidebarRescueObserver) {
          window.__audioscriptSidebarRescueObserver = true;
          const observer = new MutationObserver(revealSidebarControl);
          if (document.body) {
            observer.observe(document.body, {
              attributes: true,
              childList: true,
              subtree: true
            });
          }
          window.setInterval(revealSidebarControl, 1000);
          window.addEventListener("resize", revealSidebarControl);
        }
        revealSidebarControl();
        setTimeout(revealSidebarControl, 250);
        setTimeout(revealSidebarControl, 900);
        setTimeout(revealSidebarControl, 1800);
        """,
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

def render_rotary_dial(label, current_value, options, key_prefix, suffix=""):
    """Dibuja un dial rotativo usando solo controles de giro."""
    normalized_options = [
        option if isinstance(option, tuple) else (str(option), option)
        for option in options
    ]
    values = [value for _, value in normalized_options]
    labels = [option_label for option_label, _ in normalized_options]

    if current_value not in values:
        current_value = values[0]

    current_index = values.index(current_value)
    current_label = labels[current_index]
    dial_marks = []
    mark_positions = {
        2: [(18, 84), (82, 84)],
        3: [(50, 8), (15, 86), (85, 86)],
        4: [(50, 8), (92, 50), (50, 94), (8, 50)],
        5: [(50, 6), (96, 43), (76, 96), (24, 96), (4, 43)],
    }
    if len(labels) <= 5:
        visible_options = list(enumerate(labels))
        positions = mark_positions[len(visible_options)]
    else:
        visible_indexes = [
            current_index,
            (current_index + 1) % len(labels),
            (current_index + 2) % len(labels),
            (current_index - 2) % len(labels),
            (current_index - 1) % len(labels),
        ]
        visible_options = [(index, labels[index]) for index in visible_indexes]
        positions = mark_positions[5]

    for mark_index, (option_index, option_label) in enumerate(visible_options):
        active_class = " dial-mark--active" if option_index == current_index else ""
        left, top = positions[mark_index]
        dial_marks.append(
            f'<span class="dial-mark dial-mark--{mark_index}{active_class}" style="left:{left}%;top:{top}%;">{html.escape(str(option_label))}</span>'
        )
    marks_html = "".join(dial_marks)
    pointer_angle = round((current_index / max(len(values), 1)) * 360, 2)
    st.markdown(
        f"""
        <div class="dial-card">
          <div class="dial-title">{label}</div>
          <div class="dial-face">
            <div class="dial-pointer" style="transform: rotate({pointer_angle}deg);"></div>
            {marks_html}
            <div class="dial-center">{html.escape(str(current_label))}{suffix}</div>
          </div>
          <div class="dial-current">Sintonía: {html.escape(str(current_label))}{suffix}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dial-turn-row">', unsafe_allow_html=True)
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button("↺", key=f"{key_prefix}_prev", help=f"Girar {label} hacia atrás"):
            return values[(current_index - 1) % len(values)]
    with next_col:
        if st.button("↻", key=f"{key_prefix}_next", help=f"Girar {label} hacia adelante"):
            return values[(current_index + 1) % len(values)]
    st.markdown("</div>", unsafe_allow_html=True)

    return current_value

def select_dial_option(label, current_value, options, key_prefix):
    """Compatibilidad para selectores existentes basados en dial."""
    return render_rotary_dial(label, current_value, options, key_prefix)

def render_font_size_dial():
    """Controla el tamano de letra desde un dial compacto."""
    return render_rotary_dial(
        "Tamaño de letra",
        st.session_state.sidebar_editor_font_size,
        [(f"{size}px", size) for size in range(12, 29)],
        "font_size_dial",
    )

def render_segment_minutes_dial():
    """Controla la duracion de segmentos con el mismo patron de dial."""
    return render_rotary_dial(
        "Tiempo por segmento",
        st.session_state.sidebar_segment_mins,
        [(f"{minutes} min", minutes) for minutes in range(1, 31)],
        "segment_minutes_dial",
    )

def render_sidebar_minute_ring(minutes):
    st.markdown(
        f"""
        <div class="sidebar-minute-ring">
          <div class="sidebar-minute-ring__inner">{int(minutes)}'</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def open_card(title, tone="default"):
    card_class = "section-card"
    if tone != "default":
        card_class = f"{card_class} section-card--{tone}"
    st.markdown(
        f'<div class="{card_class}"><div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )

def close_card():
    st.markdown("</div>", unsafe_allow_html=True)

def render_selectable_transcript_panel(text, highlight_term="", reading_mode=False):
    """Muestra el texto transcrito como bloque seleccionable para codificar con mouse."""
    # Deuda técnica consciente:
    # Este panel conversa con la UI principal buscando inputs de Streamlit dentro de
    # window.parent.document por aria-label. Si Streamlit cambia esos aria-label, el
    # DOM resultante o endurece el sandbox del iframe, la selección y la codificación
    # dejarán de sincronizarse aunque el resto de la pantalla siga renderizando.
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
    panel_background = (
        "linear-gradient(90deg, rgba(196,89,55,0.12) 1px, transparent 1px) 42px 0 / 1px 100%, "
        "repeating-linear-gradient(#f5efe3, #f5efe3 31px, #e2d7c1 32px)"
        if reading_mode
        else "linear-gradient(90deg, rgba(196,89,55,0.16) 1px, transparent 1px) 42px 0 / 1px 100%, "
        "repeating-linear-gradient(#fffdf8, #fffdf8 31px, #e7decc 32px)"
    )
    panel_border = (
        "1px solid rgba(145, 117, 67, 0.22)"
        if reading_mode
        else "1px solid rgba(37,42,50,.13)"
    )
    panel_text_color = "#4e5a67" if reading_mode else "#263238"
    panel_font_size = 19 if reading_mode else 17
    panel_line_height = 1.5 if reading_mode else 1.82
    panel_shadow = (
        "inset 0 1px 0 rgba(255,255,255,.55), 0 10px 24px rgba(118,95,56,.10)"
        if reading_mode
        else "none"
    )
    panel_width_rule = "width:100%; max-width:100%; margin:0;" if reading_mode else ""
    panel_padding = (
        "30px max(18%, calc((100% - 39rem) / 2))"
        if reading_mode
        else "24px 28px 24px 58px"
    )
    content_width_rule = "max-width:66ch; margin:0 auto;" if reading_mode else ""
    render_dom_html(
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
            max-height:495px;
            overflow:auto;
            background:{panel_background};
            border:{panel_border};
            border-radius:16px;
            padding:{panel_padding};
            color:{panel_text_color};
            font-family:Georgia, 'Iowan Old Style', serif;
            font-size:{panel_font_size}px;
            line-height:{panel_line_height};
            box-shadow:{panel_shadow};
            white-space:normal;
            user-select:text;
            {panel_width_rule}
          "><div style="{content_width_rule}">{safe_text}</div></div>
        </div>
        <script>
        const parentDoc = document;
        const transcriptEl = document.getElementById("selectable-transcript");
        const toolbarEl = document.getElementById("selection-toolbar");
        const codeButtonEl = document.getElementById("selection-code-btn");
        let currentSelection = "";

        function setStreamlitField(label, value) {{
          // Fragilidad conocida: dependemos de aria-label estables generados por Streamlit.
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

        function revealCodingPanel() {{
          const anchor = parentDoc.getElementById('audioscript-code-panel-anchor');
          const quoteField = parentDoc.querySelector('textarea[aria-label="Cita o frase a codificar"]');
          const codeField = parentDoc.querySelector('input[aria-label="Código"]');
          const focusTarget = quoteField || codeField || anchor;
          if (!focusTarget) return false;

          focusTarget.scrollIntoView({{
            behavior: "smooth",
            block: "center",
            inline: "nearest"
          }});

          setTimeout(() => {{
            if (quoteField) {{
              quoteField.focus();
            }}
            if (codeField) {{
              codeField.focus();
            }}
            focusTarget.scrollIntoView({{
              behavior: "smooth",
              block: "center",
              inline: "nearest"
            }});
            const highlightTarget = focusTarget;
            highlightTarget.style.boxShadow = "0 0 0 4px rgba(84, 212, 167, 0.28)";
            highlightTarget.style.transition = "box-shadow .22s ease";
            setTimeout(() => {{
              highlightTarget.style.boxShadow = "";
            }}, 1600);
          }}, 380);
          return true;
        }}

        function focusCodeField() {{
          const anchor = parentDoc.getElementById('audioscript-code-panel-anchor');
          const quoteField = parentDoc.querySelector('textarea[aria-label="Cita o frase a codificar"]');
          const codeField = parentDoc.querySelector('input[aria-label="Código"]');
          const focusTarget = quoteField || codeField || anchor;
          if (!focusTarget) return;

          focusTarget.scrollIntoView({{
            behavior: "smooth",
            block: "center",
            inline: "nearest"
          }});

          setTimeout(() => {{
            if (quoteField) quoteField.focus();
            if (codeField) codeField.focus();
            focusTarget.scrollIntoView({{
              behavior: "smooth",
              block: "center",
              inline: "nearest"
            }});
            const highlightTarget = focusTarget;
            highlightTarget.style.boxShadow = "0 0 0 4px rgba(84, 212, 167, 0.28)";
            highlightTarget.style.transition = "box-shadow .22s ease";
            setTimeout(() => {{
              highlightTarget.style.boxShadow = "";
            }}, 1600);
          }}, 380);
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
        allow_js=True,
    )

def render_code_selection_from_editor(source_label=None, *, runtime_only=False):
    """Permite editar o codificar texto seleccionado directamente desde el editor."""
    if not runtime_only:
        render_dom_html(
            """
            <div style="font-size:12px;color:#5d6876;margin:4px 0 12px 0;">
              Selecciona una frase dentro del editor para abrir la barra flotante de edición. Los cambios de formato se reflejarán en el .docx
            </div>
            """
        )
        return

    source_labels_json = json.dumps(
        [
            "Edite este fragmento antes de continuar",
            "Edite el texto si es necesario",
            "Contenido consolidado",
        ],
        ensure_ascii=False,
    )
    components.html(
        f"""
        <script>
        (() => {{
        const parentWindow = window.parent;
        const parentDoc = window.parent.document;
        parentWindow.__audioscriptFloatingSelectionScriptLoaded = true;
        const sourceLabels = {source_labels_json};
        const toolbarId = "audioscript-floating-selection-toolbar";
        const selectionState = parentWindow.__audioscriptFloatingSelectionState || {{
          lastSelection: null,
          boundEditors: new WeakSet()
        }};
        parentWindow.__audioscriptFloatingSelectionState = selectionState;

        function setStreamlitField(label, value) {{
          const target = parentDoc.querySelector(`textarea[aria-label="${{label}}"], input[aria-label="${{label}}"]`);
          if (!target) return false;
          const nativeSetter = Object.getOwnPropertyDescriptor(
            target.tagName === "TEXTAREA"
              ? parentWindow.HTMLTextAreaElement.prototype
              : parentWindow.HTMLInputElement.prototype,
            "value"
          ).set;
          nativeSetter.call(target, value);
          target.dispatchEvent(new parentWindow.Event("input", {{ bubbles: true }}));
          target.dispatchEvent(new parentWindow.Event("change", {{ bubbles: true }}));
          return true;
        }}

        function setEditorValue(editor, value) {{
          const nativeSetter = Object.getOwnPropertyDescriptor(parentWindow.HTMLTextAreaElement.prototype, "value").set;
          nativeSetter.call(editor, value);
          editor.dispatchEvent(new parentWindow.Event("input", {{ bubbles: true }}));
          editor.dispatchEvent(new parentWindow.Event("change", {{ bubbles: true }}));
        }}

        function findEditor() {{
          const editors = Array.from(parentDoc.querySelectorAll("textarea")).filter(
            (editor) => sourceLabels.includes(editor.getAttribute("aria-label"))
          );
          return editors.find((editor) => parentDoc.activeElement === editor) || editors[editors.length - 1];
        }}

        function selectedInfo(editor) {{
          const start = editor.selectionStart || 0;
          const end = editor.selectionEnd || 0;
          const selected = editor.value.substring(start, end);
          return {{ start, end, selected }};
        }}

        function rememberSelection(editor) {{
          const info = selectedInfo(editor);
          if (info.selected.trim() && info.end > info.start) {{
            selectionState.lastSelection = {{
              editor,
              start: info.start,
              end: info.end,
              selected: info.selected
            }};
            return selectionState.lastSelection;
          }}
          return selectionState.lastSelection;
        }}

        function ensureToolbar() {{
          let toolbar = parentDoc.getElementById(toolbarId);
          if (toolbar) return toolbar;
          toolbar = parentDoc.createElement("div");
          toolbar.id = toolbarId;
          toolbar.style.cssText = [
            "position:fixed",
            "display:none",
            "align-items:center",
            "gap:8px",
            "z-index:999999",
            "padding:8px",
            "border-radius:14px",
            "background:#102f53",
            "box-shadow:0 14px 34px rgba(16,47,83,.28)",
            "border:1px solid rgba(255,255,255,.22)"
          ].join(";");
          toolbar.innerHTML = `
            <button type="button" data-action="bold" title="Negritas" aria-label="Negritas"><strong>B</strong></button>
            <button type="button" data-action="underline" title="Subrayado" aria-label="Subrayado">
              <span style="text-decoration:underline;text-underline-offset:3px;font-weight:900;">U</span>
            </button>
            <button type="button" data-action="highlight" title="Resaltar amarillo" aria-label="Resaltar amarillo">
              <svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true">
                <path d="M4 17l8.8-8.8 3 3L7 20H4v-3z" fill="currentColor"></path>
                <path d="M14.2 6.8l1.4-1.4a1.4 1.4 0 0 1 2 0l1 1a1.4 1.4 0 0 1 0 2l-1.4 1.4-3-3z" fill="currentColor"></path>
                <path d="M3 21h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
              </svg>
            </button>
            <button type="button" data-action="strike" title="Tachado" aria-label="Tachado">
              <span style="text-decoration:line-through;font-weight:900;">T</span>
            </button>
            <span style="width:1px;height:28px;background:rgba(255,255,255,.28);display:inline-block;"></span>
            <button type="button" data-action="code" title="Codificar selección" aria-label="Codificar selección">
              <svg viewBox="0 0 24 24" width="21" height="21" aria-hidden="true">
                <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h6.2c.4 0 .8.2 1.1.5l6.7 6.7a1.7 1.7 0 0 1 0 2.4l-5.9 5.9a1.7 1.7 0 0 1-2.4 0l-6.7-6.7a1.6 1.6 0 0 1-.5-1.1V5.5z" fill="currentColor"></path>
                <circle cx="8" cy="8" r="1.5" fill="#102f53"></circle>
              </svg>
            </button>
          `;
          toolbar.querySelectorAll("button").forEach((button) => {{
            button.style.cssText = [
              "border:none",
              "border-radius:8px",
              "width:40px",
              "height:38px",
              "display:inline-grid",
              "place-items:center",
              "font-size:18px",
              "font-weight:900",
              "color:#f6fbff",
              "background:#1d3f63",
              "cursor:pointer",
              "transition:all .16s ease"
            ].join(";");
          }});
          toolbar.addEventListener("mousedown", (event) => {{
            event.preventDefault();
          }});
          toolbar.querySelector('[data-action="highlight"]').style.color = "#ffe58a";
          toolbar.querySelector('[data-action="underline"]').style.color = "#d8ecff";
          toolbar.querySelector('[data-action="strike"]').style.color = "#ffd2d2";
          toolbar.querySelector('[data-action="code"]').style.color = "#54d4a7";
          parentDoc.body.appendChild(toolbar);
          return toolbar;
        }}

        function hideToolbar() {{
          const toolbar = parentDoc.getElementById(toolbarId);
          if (toolbar) toolbar.style.display = "none";
        }}

        function positionToolbar(editor, event) {{
          const toolbar = ensureToolbar();
          const editorRect = editor.getBoundingClientRect();
          const toolbarWidth = 306;
          const left = Math.min(
            Math.max((event && event.clientX ? event.clientX : editorRect.left + editorRect.width - toolbarWidth), 12),
            parentDoc.documentElement.clientWidth - toolbarWidth - 12
          );
          const top = Math.max((event && event.clientY ? event.clientY - 54 : editorRect.top - 48), 12);
          toolbar.style.left = `${{left}}px`;
          toolbar.style.top = `${{top}}px`;
          toolbar.style.display = "flex";
          toolbar.dataset.sourceLabel = editor.getAttribute("aria-label") || "";
        }}

        function updateToolbar(event) {{
          const editor = findEditor();
          if (!editor) return;
          const info = selectedInfo(editor);
          if (info.selected.trim() && info.end > info.start) {{
            rememberSelection(editor);
            positionToolbar(editor, event);
            return;
          }}
          hideToolbar();
        }}

        function bindEditor(editor) {{
          if (!editor || selectionState.boundEditors.has(editor)) return;
          const handler = (event) => updateToolbar(event);
          editor.addEventListener("mouseup", handler);
          editor.addEventListener("keyup", handler);
          editor.addEventListener("touchend", handler);
          editor.addEventListener("select", handler);
          editor.addEventListener("focus", handler);
          selectionState.boundEditors.add(editor);
        }}

        function bindEditors() {{
          const editors = Array.from(parentDoc.querySelectorAll("textarea")).filter(
            (editor) => sourceLabels.includes(editor.getAttribute("aria-label"))
          );
          editors.forEach(bindEditor);
          const toolbar = parentDoc.getElementById(toolbarId);
          if (toolbar) toolbar.dataset.boundEditorCount = String(editors.length);
          return editors;
        }}

        function wrapSelection(before, after) {{
          const remembered = selectionState.lastSelection;
          if (!remembered || !remembered.editor) return;
          const editor = remembered.editor;
          const info = {{
            start: remembered.start,
            end: remembered.end,
            selected: remembered.selected
          }};
          if (!info.selected.trim() || info.end <= info.start) return;
          const value = editor.value;
          const replacement = `${{before}}${{info.selected}}${{after}}`;
          setEditorValue(
            editor,
            value.slice(0, info.start) + replacement + value.slice(info.end)
          );
          editor.focus();
          editor.setSelectionRange(info.start + before.length, info.start + before.length + info.selected.length);
          selectionState.lastSelection = null;
          hideToolbar();
        }}

        ensureToolbar().onclick = function(event) {{
          const button = event.target.closest("button[data-action]");
          if (!button) return;
          const editor = findEditor() || (selectionState.lastSelection ? selectionState.lastSelection.editor : null);
          if (!editor) return;
          const info = rememberSelection(editor) || selectedInfo(editor);
          const selected = info.selected.trim();
          if (!selected) {{
            editor.focus();
            hideToolbar();
            return;
          }}
          if (button.dataset.action === "code") {{
            const updated = setStreamlitField("Cita o frase a codificar", selected);
            if (updated) {{
              revealCodingPanel();
            }} else {{
              alert("Abre el panel de Codificación para pegar la cita seleccionada.");
            }}
            hideToolbar();
            return;
          }}
          if (button.dataset.action === "bold") {{
            wrapSelection("**", "**");
            return;
          }}
          if (button.dataset.action === "underline") {{
            wrapSelection("__", "__");
            return;
          }}
          if (button.dataset.action === "highlight") {{
            wrapSelection("==", "==");
            return;
          }}
          if (button.dataset.action === "strike") {{
            wrapSelection("~~", "~~");
          }}
        }};

        function shouldHandleSelectionEvent(event) {{
          const target = event && event.target;
          if (!target || target.tagName !== "TEXTAREA") return false;
          return sourceLabels.includes(target.getAttribute("aria-label"));
        }}

        function handleGlobalSelectionEvent(event) {{
          if (!shouldHandleSelectionEvent(event)) return;
          updateToolbar(event);
        }}

        if (!parentWindow.__audioscriptFloatingSelectionBound) {{
          parentWindow.__audioscriptFloatingSelectionBound = true;
          parentDoc.addEventListener("mouseup", handleGlobalSelectionEvent, true);
          parentDoc.addEventListener("keyup", handleGlobalSelectionEvent, true);
          parentDoc.addEventListener("touchend", handleGlobalSelectionEvent, true);
          parentDoc.addEventListener("select", handleGlobalSelectionEvent, true);
          parentDoc.addEventListener("selectionchange", () => {{
            const editor = findEditor();
            if (!editor || parentDoc.activeElement !== editor) return;
            updateToolbar();
          }}, true);
          parentDoc.addEventListener("blur", (event) => {{
            if (!shouldHandleSelectionEvent(event)) return;
            setTimeout(() => {{
              const toolbar = parentDoc.getElementById(toolbarId);
              if (toolbar && !toolbar.matches(":hover")) hideToolbar();
            }}, 320);
          }}, true);
          parentWindow.setInterval(bindEditors, 1200);
        }}

        const runtimeToolbar = ensureToolbar();
        runtimeToolbar.dataset.runtimeReady = "true";
        if (!runtimeToolbar.__audioscriptEditorObserver && parentDoc.body) {{
          const editorObserver = new parentWindow.MutationObserver(() => bindEditors());
          editorObserver.observe(parentDoc.body, {{ childList: true, subtree: true }});
          runtimeToolbar.__audioscriptEditorObserver = editorObserver;
        }}
        bindEditors();
        setTimeout(() => {{
          const editor = findEditor();
          if (editor && selectedInfo(editor).selected.trim()) updateToolbar();
        }}, 200);
        }})();
        </script>
        """,
        height=1,
    )

def render_segment_audio_player(audio_path):
    """Muestra el audio del segmento actual con saltos rapidos."""
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    extension = os.path.splitext(audio_path)[1].lower().replace(".", "") or "wav"
    audio_format = "audio/mpeg" if extension == "mp3" else f"audio/{extension}"
    st.audio(audio_bytes, format=audio_format)
    render_dom_html(
        """
        <div style="display:flex; gap:8px; align-items:center; margin-top:4px; flex-wrap:wrap;">
          <button id="segment-audio-back" style="padding:6px 10px;">-5 s</button>
          <button id="segment-audio-toggle" style="padding:6px 10px;">Play / Pause</button>
          <button id="segment-audio-forward" style="padding:6px 10px;">+5 s</button>
          <span style="font-size:12px; color:#555;">Atajos: Alt + Flecha izquierda/derecha</span>
        </div>
        <script>
        function latestAudioElement() {
          const audios = document.querySelectorAll("audio");
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
        document.getElementById("segment-audio-back")?.addEventListener("click", () => controlSegmentAudio(-5));
        document.getElementById("segment-audio-toggle")?.addEventListener("click", toggleSegmentAudio);
        document.getElementById("segment-audio-forward")?.addEventListener("click", () => controlSegmentAudio(5));
        </script>
        """,
        allow_js=True,
    )

def render_keyboard_shortcuts(segment_mode_active):
    """Activa atajos de teclado para acelerar la revisión."""
    confirm_label = "Confirmar y Siguiente" if segment_mode_active else "Iniciar Transcripción Completa"
    render_dom_script(
        f"""
        const parentWindow = window;
        const parentDoc = document;
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
        """,
    )

def highlight_transcribe_buttons():
    """Distingue visualmente los botones accionables principales."""
    render_dom_script(
        """
        function markActionButtons() {
          const doc = document;
          Array.from(doc.querySelectorAll("button")).forEach((button) => {
            const text = (button.innerText || "").trim();
            if (
              text === "Transcribir" ||
              text === "Iniciar Transcripción Completa" ||
              text === "Transcribir este fragmento"
            ) {
              button.classList.add("audioscript-transcribe-button");
              button.style.setProperty("background", "linear-gradient(135deg, #e94b33 0%, #b73525 100%)", "important");
              button.style.setProperty("border", "1px solid #9f2c1f", "important");
              button.style.setProperty("color", "white", "important");
              button.style.setProperty("box-shadow", "0 16px 30px rgba(200,70,48,0.34), 0 0 0 4px rgba(200,70,48,0.08)", "important");
              button.style.setProperty("font-weight", "950", "important");
              button.querySelectorAll("*").forEach((child) => {
                child.style.setProperty("color", "white", "important");
                child.style.setProperty("font-weight", "950", "important");
              });
            }
            if (text === "↳") {
              button.classList.add("audioscript-replace-button");
              button.setAttribute("title", "Aplicar reemplazo");
              button.setAttribute("aria-label", "Aplicar reemplazo");
            }
          });
        }
        if (!window.__audioscriptActionButtonObserver) {
          window.__audioscriptActionButtonObserver = true;
          const observer = new MutationObserver(markActionButtons);
          observer.observe(document.body, {
            childList: true,
            subtree: true
          });
          window.setInterval(markActionButtons, 900);
        }
        markActionButtons();
        setTimeout(markActionButtons, 250);
        setTimeout(markActionButtons, 900);
        """,
    )

def open_analysis_desk(segment_label="segmento activo"):
    """Agrupa memoing y codificación junto al texto que se está leyendo."""
    st.markdown(
        '<div class="analysis-desk is-coding-target" data-audioscript-analysis-desk="true">',
        unsafe_allow_html=True,
    )

def close_analysis_desk():
    st.markdown("</div>", unsafe_allow_html=True)

def render_segmented_or_fallback(label, options, current_value, key, help_text=None):
    if hasattr(st, "segmented_control"):
        return st.segmented_control(
            label,
            options=options,
            default=current_value if current_value in options else options[0],
            key=key,
            help=help_text,
            selection_mode="single",
        )
    return st.radio(
        label,
        options=options,
        index=options.index(current_value) if current_value in options else 0,
        key=key,
        help=help_text,
        horizontal=True,
    )
