from pathlib import Path

import streamlit as st


STYLESHEET_PATH = Path(__file__).parent / "assets" / "app.css"


def apply_global_styles():
    """Inyecta la hoja visual global de AudioScript Contextual."""
    css = STYLESHEET_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
