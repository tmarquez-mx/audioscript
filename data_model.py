import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime

import streamlit as st

from media import get_media_metadata
from shared_config import (
    AUDIO_SEGMENT_FORMAT,
    BYTES_PER_MB,
    DEFAULT_TRANSCRIPTION_LANGUAGE,
    DEFAULT_WHISPER_MODEL,
    MODE_SEGMENTED,
    normalize_processing_mode,
    sanitize_filename,
)


APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.environ.get(
    "AUDIOSCRIPT_DATA_DIR",
    os.path.join(APP_DIR, ".audioscript_projects"),
)
os.makedirs(PROJECTS_DIR, exist_ok=True)
QUICK_SPLIT_ROOT = os.path.join(tempfile.gettempdir(), "audioscript_splits")
os.makedirs(QUICK_SPLIT_ROOT, exist_ok=True)

PROJECT_SETTINGS_DEFAULTS = {
    "mode": MODE_SEGMENTED,
    "model": DEFAULT_WHISPER_MODEL,
    "language": DEFAULT_TRANSCRIPTION_LANGUAGE,
    "trans_type": "Limpia (Sin muletillas)",
    "segment_mins": 5,
    "editor_font_size": 16,
    "custom_terms": "",
    "reading_mode": False,
    "prep_confirmed": False,
    "transcription_started": False,
}

PROJECT_SETTINGS_SESSION_MAP = {
    "mode": "sidebar_mode",
    "model": "sidebar_model_choice",
    "language": "sidebar_language_choice",
    "trans_type": "sidebar_trans_type",
    "segment_mins": "sidebar_segment_mins",
    "editor_font_size": "sidebar_editor_font_size",
    "custom_terms": "main_custom_terms",
    "reading_mode": "reading_mode_enabled",
}


def build_project_id(uploaded_file):
    """Crea un identificador estable para el proyecto del archivo cargado."""
    raw_id = f"{uploaded_file.name}-{uploaded_file.size}"
    return hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:16]

def build_named_project_id(project_name):
    """Crea un identificador estable y legible para un proyecto."""
    base = sanitize_filename(
        project_name,
        preserve_extension=False,
        default_name="proyecto",
    ).rsplit(".", 1)[0].lower()
    fingerprint = hashlib.sha1(
        f"{project_name}-{datetime.now().isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"{base[:38] or 'proyecto'}-{fingerprint}"

def get_project_dir(project_id):
    return os.path.join(PROJECTS_DIR, project_id)

def get_project_state_path(project_id):
    return os.path.join(get_project_dir(project_id), "state.json")

def get_project_meta_path(project_id):
    return os.path.join(get_project_dir(project_id), "project.json")

def get_project_legacy_state_path(project_id):
    return os.path.join(get_project_dir(project_id), "state.legacy.json")

def get_project_materials_root_dir(project_id):
    return os.path.join(get_project_dir(project_id), "materials")

def get_material_dir(project_id, material_id):
    return os.path.join(get_project_materials_root_dir(project_id), material_id)

def get_material_transcription_path(project_id, material_id):
    return os.path.join(get_material_dir(project_id, material_id), "transcription.json")

def get_project_chunks_dir(project_id, material_id=None):
    if material_id is None:
        material_id = st.session_state.get("active_material_id")
    if material_id:
        return os.path.join(get_material_dir(project_id, material_id), "chunks")
    return os.path.join(get_project_dir(project_id), "chunks")

def get_project_audio_path(project_id, original_name):
    extension = os.path.splitext(original_name)[1] or ".audio"
    return os.path.join(get_project_dir(project_id), f"source{extension}")

def get_project_media_dir(project_id):
    return os.path.join(get_project_dir(project_id), "media")

def get_project_quick_split_dir(project_id):
    return os.path.join(
        QUICK_SPLIT_ROOT,
        sanitize_filename(project_id, preserve_extension=False, default_name="proyecto").rsplit(".", 1)[0],
    )

def get_project_media_path(project_id, original_name):
    safe_filename = sanitize_filename(
        original_name,
        preserve_extension=True,
        default_name="material",
        default_extension=".audio",
    )
    fingerprint = hashlib.sha1(original_name.encode("utf-8")).hexdigest()[:8]
    return os.path.join(get_project_media_dir(project_id), f"{fingerprint}_{safe_filename}")

def display_media_name(media_path):
    """Quita el prefijo técnico de los archivos guardados."""
    filename = os.path.basename(media_path)
    return re.sub(r"^[0-9a-f]{8}_", "", filename)

def build_material_id(material_name, seed=""):
    """Crea un identificador estable y legible para un material dentro del proyecto."""
    base = sanitize_filename(
        material_name,
        preserve_extension=False,
        default_name="material",
    ).rsplit(".", 1)[0].lower()
    fingerprint = hashlib.sha1(
        f"{material_name}-{seed or datetime.now().isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"{base[:38] or 'material'}-{fingerprint}"

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def normalize_project_date(date_value):
    if not date_value:
        return ""
    if hasattr(date_value, "isoformat"):
        return date_value.isoformat()
    return str(date_value)

def get_relative_project_path(project_id, absolute_path):
    if not absolute_path:
        return ""
    project_dir = get_project_dir(project_id)
    try:
        return os.path.relpath(absolute_path, project_dir)
    except ValueError:
        return absolute_path

def resolve_project_path(project_id, stored_path):
    if not stored_path:
        return ""
    if os.path.isabs(stored_path):
        return stored_path
    return os.path.join(get_project_dir(project_id), stored_path)

def format_size_mb(size_bytes):
    """Devuelve un tamaño legible en MB."""
    return f"{size_bytes / BYTES_PER_MB:.1f} MB"

def scan_project_media_files(project_id):
    """Escanea el disco como respaldo para proyectos aún no migrados."""
    media_dir = get_project_media_dir(project_id)
    quick_split_dir = get_project_quick_split_dir(project_id)
    media_files = []
    for directory in (media_dir, quick_split_dir):
        if not os.path.isdir(directory):
            continue
        media_files.extend(
            [
                os.path.join(directory, filename)
                for filename in os.listdir(directory)
                if not filename.startswith(".")
            ]
        )
    return sorted(
        media_files,
        key=os.path.getmtime,
        reverse=True,
    )

def list_project_media(project_id):
    """Lista rutas de materiales guardados dentro del proyecto."""
    project_meta = load_project_meta(project_id)
    if project_meta and project_meta.get("schema_version") == 2:
        indexed_paths = [
            resolve_project_path(project_id, material.get("path", ""))
            for material in project_meta.get("materials", [])
            if material.get("path")
        ]
        if indexed_paths:
            return sorted(
                indexed_paths,
                key=lambda path: os.path.getmtime(path) if os.path.exists(path) else 0,
                reverse=True,
            )

    return scan_project_media_files(project_id)

def empty_material_transcription_state(material_id=""):
    return {
        "material_id": material_id,
        "chunks_prepared": False,
        "chunk_segment_mins": None,
        "current_chunk_idx": 0,
        "transcript_segments": [],
        "segment_texts": [],
        "current_segment_text": "",
        "memos": [],
        "codes": [],
        "last_transcription": "",
        "updated": now_iso(),
    }

def get_default_project_settings():
    return PROJECT_SETTINGS_DEFAULTS.copy()


def get_default_session_setting_state():
    return {
        "sidebar_mode": PROJECT_SETTINGS_DEFAULTS["mode"],
        "sidebar_model_choice": PROJECT_SETTINGS_DEFAULTS["model"],
        "sidebar_language_choice": PROJECT_SETTINGS_DEFAULTS["language"],
        "sidebar_trans_type": PROJECT_SETTINGS_DEFAULTS["trans_type"],
        "sidebar_segment_mins": PROJECT_SETTINGS_DEFAULTS["segment_mins"],
        "sidebar_editor_font_size": PROJECT_SETTINGS_DEFAULTS["editor_font_size"],
        "main_custom_terms": PROJECT_SETTINGS_DEFAULTS["custom_terms"],
        "reading_mode_enabled": PROJECT_SETTINGS_DEFAULTS["reading_mode"],
    }


def normalize_project_settings(settings=None):
    normalized = get_default_project_settings()
    normalized.update(settings or {})
    normalized["mode"] = normalize_processing_mode(normalized.get("mode", normalized["mode"]))

    try:
        normalized["segment_mins"] = int(normalized.get("segment_mins", PROJECT_SETTINGS_DEFAULTS["segment_mins"]))
    except (TypeError, ValueError):
        normalized["segment_mins"] = PROJECT_SETTINGS_DEFAULTS["segment_mins"]

    try:
        normalized["editor_font_size"] = int(
            normalized.get("editor_font_size", PROJECT_SETTINGS_DEFAULTS["editor_font_size"])
        )
    except (TypeError, ValueError):
        normalized["editor_font_size"] = PROJECT_SETTINGS_DEFAULTS["editor_font_size"]

    normalized["model"] = str(normalized.get("model", PROJECT_SETTINGS_DEFAULTS["model"]) or PROJECT_SETTINGS_DEFAULTS["model"])
    normalized["language"] = str(
        normalized.get("language", PROJECT_SETTINGS_DEFAULTS["language"]) or PROJECT_SETTINGS_DEFAULTS["language"]
    )
    normalized["trans_type"] = str(
        normalized.get("trans_type", PROJECT_SETTINGS_DEFAULTS["trans_type"]) or PROJECT_SETTINGS_DEFAULTS["trans_type"]
    )
    normalized["custom_terms"] = str(
        normalized.get("custom_terms", PROJECT_SETTINGS_DEFAULTS["custom_terms"]) or ""
    )
    normalized["reading_mode"] = bool(normalized.get("reading_mode", PROJECT_SETTINGS_DEFAULTS["reading_mode"]))
    normalized["prep_confirmed"] = bool(
        normalized.get("prep_confirmed", PROJECT_SETTINGS_DEFAULTS["prep_confirmed"])
    )
    normalized["transcription_started"] = bool(
        normalized.get("transcription_started", PROJECT_SETTINGS_DEFAULTS["transcription_started"])
    )
    return normalized


def project_settings_to_session_state(settings=None):
    normalized = normalize_project_settings(settings)
    return {
        session_key: normalized[setting_key]
        for setting_key, session_key in PROJECT_SETTINGS_SESSION_MAP.items()
    }


def build_project_settings_from_session(session_state_obj, existing_settings=None):
    normalized = normalize_project_settings(existing_settings)
    for setting_key, session_key in PROJECT_SETTINGS_SESSION_MAP.items():
        if session_key in session_state_obj:
            normalized[setting_key] = session_state_obj.get(session_key)
    return normalize_project_settings(normalized)


def build_project_settings_from_legacy_state(legacy_state, existing_settings=None):
    normalized = normalize_project_settings(existing_settings)
    for setting_key, session_key in PROJECT_SETTINGS_SESSION_MAP.items():
        if session_key in (legacy_state or {}):
            normalized[setting_key] = legacy_state.get(session_key)
    return normalize_project_settings(normalized)


def bind_annotations_to_material(items, material_id):
    """Asigna el material activo a memos y códigos legados que no lo tenían."""
    normalized = []
    for item in items or []:
        if isinstance(item, dict):
            entry = item.copy()
            entry["material_id"] = entry.get("material_id") or material_id
            normalized.append(entry)
        else:
            normalized.append(item)
    return normalized

def load_project_meta(project_id):
    meta_path = get_project_meta_path(project_id)
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, "r", encoding="utf-8") as project_file:
        return json.load(project_file)

def load_material_transcription(project_id, material_id):
    transcription_path = get_material_transcription_path(project_id, material_id)
    if not os.path.exists(transcription_path):
        return empty_material_transcription_state(material_id)
    with open(transcription_path, "r", encoding="utf-8") as material_file:
        state = json.load(material_file)
    merged = empty_material_transcription_state(material_id)
    merged.update(state)
    merged["material_id"] = material_id
    merged["memos"] = bind_annotations_to_material(merged.get("memos", []), material_id)
    merged["codes"] = bind_annotations_to_material(merged.get("codes", []), material_id)
    return merged


def save_material_transcription_document(project_id, material_id, material_state):
    """Persiste el estado serializado de un material."""
    if not project_id or not material_id:
        return
    os.makedirs(get_material_dir(project_id, material_id), exist_ok=True)
    with open(get_material_transcription_path(project_id, material_id), "w", encoding="utf-8") as material_file:
        json.dump(material_state, material_file, ensure_ascii=True, indent=2)


def save_project_meta_document(project_id, project_meta):
    """Persiste el documento project.json del esquema vigente."""
    if not project_id or not project_meta:
        return
    os.makedirs(get_project_dir(project_id), exist_ok=True)
    with open(get_project_meta_path(project_id), "w", encoding="utf-8") as project_file:
        json.dump(project_meta, project_file, ensure_ascii=True, indent=2)


def save_legacy_state_document(project_id, project_state):
    """Mantiene state.json para compatibilidad con versiones anteriores."""
    if not project_id or not project_state:
        return
    os.makedirs(get_project_dir(project_id), exist_ok=True)
    with open(get_project_state_path(project_id), "w", encoding="utf-8") as state_file:
        json.dump(project_state, state_file, ensure_ascii=True, indent=2)

def get_material_record(project_meta, material_id):
    if not project_meta:
        return None
    for material in project_meta.get("materials", []):
        if material.get("id") == material_id:
            return material
    return None

def get_active_material_record(project_meta):
    if not project_meta:
        return None
    active_id = project_meta.get("active_material_id")
    record = get_material_record(project_meta, active_id) if active_id else None
    if record:
        return record
    materials = project_meta.get("materials", [])
    return materials[0] if materials else None

def update_material_progress(material_record):
    total_segments = len(st.session_state.get("segment_texts", []))
    transcribed_segments = sum(
        1 for text in st.session_state.get("segment_texts", []) if str(text).strip()
    )
    material_record["total_segments"] = total_segments
    material_record["transcribed_segments"] = transcribed_segments
    if total_segments and transcribed_segments >= total_segments:
        material_record["status"] = "completo"
    elif transcribed_segments > 0 or st.session_state.get("last_transcription", "").strip():
        material_record["status"] = "en_progreso"
    else:
        material_record["status"] = "pendiente"
    return material_record

def list_project_materials(project_id):
    project_meta = load_project_meta(project_id)
    if project_meta and project_meta.get("schema_version") == 2:
        materials = []
        for material in project_meta.get("materials", []):
            material_path = resolve_project_path(project_id, material.get("path", ""))
            entry = material.copy()
            entry["absolute_path"] = material_path
            materials.append(entry)
        return materials

    return [
        {
            "id": "",
            "name": display_media_name(path),
            "path": get_relative_project_path(project_id, path),
            "absolute_path": path,
            "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0,
            "duration_seconds": None,
            "added": "",
            "source": "upload",
            "split_summary": None,
            "total_segments": 0,
            "transcribed_segments": 0,
            "status": "pendiente",
        }
        for path in scan_project_media_files(project_id)
    ]

def merge_v2_project_state(project_meta, material_state):
    normalized_settings = normalize_project_settings(project_meta.get("settings", {}))
    merged_state = {
        "schema_version": 2,
        "project_id": project_meta.get("project_id", ""),
        "settings": normalized_settings,
        "active_material_id": project_meta.get("active_material_id", ""),
        "uploaded_file_id": project_meta.get("active_material_id", ""),
        "source_file_name": "",
        "source_audio_path": "",
        "main_doc_title": project_meta.get("title", "Transcripcion"),
        "project_description": project_meta.get("description", ""),
        "main_event_date": project_meta.get("event_date", ""),
        "main_transcription_date": project_meta.get("main_transcription_date", datetime.now().strftime("%d/%m/%Y %H:%M")),
        "quick_split_last_summary": project_meta.get("quick_split_last_summary", {}),
        "quick_session_mode": project_meta.get("quick_session_mode", False),
        "autosave_last_saved": project_meta.get("autosave_last_saved", ""),
    }
    merged_state.update(project_settings_to_session_state(normalized_settings))
    merged_state.update(material_state or {})
    active_material = get_active_material_record(project_meta)
    if active_material:
        merged_state["uploaded_file_id"] = active_material.get("id", "")
        merged_state["source_file_name"] = active_material.get("name", "")
        merged_state["source_audio_path"] = resolve_project_path(
            project_meta.get("project_id", ""),
            active_material.get("path", ""),
        )
    return merged_state

def migrate_project_v1_to_v2(project_id):
    existing_meta = load_project_meta(project_id)
    if existing_meta and existing_meta.get("schema_version") == 2:
        return existing_meta

    legacy_state_path = get_project_state_path(project_id)
    if not os.path.exists(legacy_state_path):
        return existing_meta

    with open(legacy_state_path, "r", encoding="utf-8") as state_file:
        legacy_state = json.load(state_file)

    project_dir = get_project_dir(project_id)
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(get_project_media_dir(project_id), exist_ok=True)
    os.makedirs(get_project_materials_root_dir(project_id), exist_ok=True)

    materials = []
    registered_paths = set()
    active_material_id = ""
    migration_timestamp = now_iso()
    legacy_saved_at = legacy_state.get("autosave_last_saved") or legacy_state.get("main_transcription_date") or migration_timestamp
    active_source_path = legacy_state.get("source_audio_path", "")
    if active_source_path and not os.path.isabs(active_source_path):
        active_source_path = resolve_project_path(project_id, active_source_path)
    active_source_name = legacy_state.get("source_file_name", "") or os.path.basename(active_source_path or "")
    active_chunks_prepared = bool(legacy_state.get("chunks_prepared"))
    active_split_summary = legacy_state.get("quick_split_last_summary") or None

    def build_material_record(file_path, source, split_summary=None, preferred_name="", total_segments=0, transcribed_segments=0):
        resolved_path = os.path.abspath(file_path) if file_path else ""
        material_name = preferred_name or display_media_name(file_path)
        material_id = build_material_id(material_name or "material", resolved_path or file_path)
        metadata = get_media_metadata(resolved_path) if resolved_path and os.path.exists(resolved_path) else {}
        size_bytes = metadata.get("size_bytes")
        if size_bytes is None and resolved_path and os.path.exists(resolved_path):
            size_bytes = os.path.getsize(resolved_path)
        status = "pendiente"
        if total_segments and transcribed_segments >= total_segments:
            status = "completo"
        elif transcribed_segments:
            status = "en_progreso"
        return {
            "id": material_id,
            "name": material_name or "Material sin título",
            "path": get_relative_project_path(project_id, resolved_path or file_path),
            "size_bytes": size_bytes or 0,
            "duration_seconds": metadata.get("duration_seconds"),
            "added": legacy_saved_at,
            "source": source,
            "split_summary": split_summary,
            "total_segments": total_segments,
            "transcribed_segments": transcribed_segments,
            "status": status,
            "updated": migration_timestamp,
        }

    if (not active_source_path or not os.path.exists(active_source_path)) and active_source_name:
        for candidate in scan_project_media_files(project_id):
            if display_media_name(candidate) == active_source_name or os.path.basename(candidate) == active_source_name:
                active_source_path = candidate
                break

    if active_source_path or active_source_name:
        material_path = active_source_path or os.path.join(
            get_project_media_dir(project_id),
            sanitize_filename(
                active_source_name,
                preserve_extension=True,
                default_name="material",
                default_extension=".audio",
            ),
        )
        transcribed_segments = sum(1 for text in legacy_state.get("segment_texts", []) if str(text).strip())
        total_segments = len(legacy_state.get("segment_texts", []))
        if not transcribed_segments and legacy_state.get("last_transcription", "").strip():
            transcribed_segments = max(1, total_segments)
        material_record = build_material_record(
            material_path,
            "quick_split" if active_chunks_prepared or active_split_summary else "upload",
            split_summary=active_split_summary,
            preferred_name=active_source_name,
            total_segments=total_segments,
            transcribed_segments=transcribed_segments,
        )
        active_material_id = material_record["id"]
        materials.append(material_record)
        if material_path:
            registered_paths.add(os.path.abspath(material_path))

        legacy_material_state = empty_material_transcription_state(active_material_id)
        legacy_material_state.update(
            {
                "chunks_prepared": legacy_state.get("chunks_prepared", False),
                "chunk_segment_mins": legacy_state.get("chunk_segment_mins"),
                "current_chunk_idx": legacy_state.get("current_chunk_idx", 0),
                "transcript_segments": legacy_state.get("transcript_segments", []),
                "segment_texts": legacy_state.get("segment_texts", []),
                "current_segment_text": legacy_state.get("current_segment_text", ""),
                "memos": bind_annotations_to_material(legacy_state.get("memos", []), active_material_id),
                "codes": bind_annotations_to_material(legacy_state.get("codes", []), active_material_id),
                "last_transcription": legacy_state.get("last_transcription", ""),
                "updated": migration_timestamp,
            }
        )
        os.makedirs(get_material_dir(project_id, active_material_id), exist_ok=True)
        with open(get_material_transcription_path(project_id, active_material_id), "w", encoding="utf-8") as material_file:
            json.dump(legacy_material_state, material_file, ensure_ascii=True, indent=2)

        legacy_chunks_dir = os.path.join(project_dir, "chunks")
        material_chunks_dir = get_project_chunks_dir(project_id, active_material_id)
        if os.path.isdir(legacy_chunks_dir) and not os.path.isdir(material_chunks_dir):
            shutil.move(legacy_chunks_dir, material_chunks_dir)

    discovered_files = []
    media_dir = get_project_media_dir(project_id)
    if os.path.isdir(media_dir):
        discovered_files.extend(
            os.path.join(media_dir, filename)
            for filename in os.listdir(media_dir)
            if not filename.startswith(".")
        )
    quick_split_dir = get_project_quick_split_dir(project_id)
    if os.path.isdir(quick_split_dir):
        for root, _, files in os.walk(quick_split_dir):
            discovered_files.extend(
                os.path.join(root, filename)
                for filename in files
                if not filename.startswith(".")
            )

    for file_path in sorted(discovered_files):
        absolute_path = os.path.abspath(file_path)
        if absolute_path in registered_paths:
            continue
        source = "quick_split" if quick_split_dir and os.path.abspath(file_path).startswith(os.path.abspath(quick_split_dir)) else "upload"
        material_record = build_material_record(file_path, source)
        materials.append(material_record)
        os.makedirs(get_material_dir(project_id, material_record["id"]), exist_ok=True)
        with open(get_material_transcription_path(project_id, material_record["id"]), "w", encoding="utf-8") as material_file:
            json.dump(empty_material_transcription_state(material_record["id"]), material_file, ensure_ascii=True, indent=2)
    project_meta = {
        "schema_version": 2,
        "project_id": project_id,
        "title": legacy_state.get("main_doc_title") or active_source_name or "Proyecto sin título",
        "description": legacy_state.get("project_description", ""),
        "event_date": normalize_project_date(legacy_state.get("main_event_date")),
        "created": existing_meta.get("created", legacy_saved_at) if existing_meta else legacy_saved_at,
        "updated": migration_timestamp,
        "active_material_id": active_material_id or (materials[0]["id"] if materials else ""),
        "settings": build_project_settings_from_legacy_state(legacy_state),
        "materials": materials,
        "quick_split_last_summary": legacy_state.get("quick_split_last_summary", {}),
        "quick_session_mode": legacy_state.get("quick_session_mode", False),
        "main_transcription_date": legacy_state.get("main_transcription_date", datetime.now().strftime("%d/%m/%Y %H:%M")),
        "autosave_last_saved": legacy_state.get("autosave_last_saved", ""),
    }

    with open(get_project_meta_path(project_id), "w", encoding="utf-8") as project_file:
        json.dump(project_meta, project_file, ensure_ascii=True, indent=2)

    if not os.path.exists(get_project_legacy_state_path(project_id)):
        shutil.copy2(legacy_state_path, get_project_legacy_state_path(project_id))

    return project_meta

def load_project_state(project_id):
    """Lee el estado guardado de un proyecto si existe."""
    project_meta = load_project_meta(project_id)
    if project_meta and project_meta.get("schema_version") == 2:
        active_material = get_active_material_record(project_meta)
        material_state = load_material_transcription(project_id, active_material.get("id", "")) if active_material else empty_material_transcription_state()
        return merge_v2_project_state(project_meta, material_state)

    state_path = get_project_state_path(project_id)
    if not os.path.exists(state_path):
        return None

    migrated_meta = migrate_project_v1_to_v2(project_id)
    if migrated_meta:
        active_material = get_active_material_record(migrated_meta)
        material_state = load_material_transcription(project_id, active_material.get("id", "")) if active_material else empty_material_transcription_state()
        return merge_v2_project_state(migrated_meta, material_state)

    with open(state_path, "r", encoding="utf-8") as state_file:
        return json.load(state_file)

def rename_project(project_id, new_title):
    if not project_id or not new_title.strip():
        return False
    project_meta = load_project_meta(project_id)
    if project_meta and project_meta.get("schema_version") == 2:
        project_meta["title"] = new_title.strip()
        project_meta["updated"] = now_iso()
        with open(get_project_meta_path(project_id), "w", encoding="utf-8") as project_file:
            json.dump(project_meta, project_file, ensure_ascii=True, indent=2)
        if st.session_state.get("current_project_id") == project_id:
            st.session_state.main_doc_title = new_title.strip()
        return True

    state = load_project_state(project_id)
    if not state:
        return False
    state["main_doc_title"] = new_title.strip()
    with open(get_project_state_path(project_id), "w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=True, indent=2)
    if st.session_state.get("current_project_id") == project_id:
        st.session_state.main_doc_title = new_title.strip()
    return True

def delete_project_state(project_id):
    """Elimina por completo el proyecto activo y sus archivos temporales."""
    if not project_id:
        return

    project_dir = get_project_dir(project_id)
    if os.path.isdir(project_dir):
        shutil.rmtree(project_dir)

def delete_material(project_id, material_id):
    """Elimina un material sin afectar el resto del proyecto."""
    project_meta = load_project_meta(project_id)
    if not project_meta or not material_id:
        return

    material_record = get_material_record(project_meta, material_id)
    if not material_record:
        return

    absolute_path = resolve_project_path(project_id, material_record.get("path", ""))
    material_dir = get_material_dir(project_id, material_id)

    if absolute_path and os.path.exists(absolute_path):
        os.remove(absolute_path)
    if os.path.isdir(material_dir):
        shutil.rmtree(material_dir)

    project_meta["materials"] = [
        material for material in project_meta.get("materials", [])
        if material.get("id") != material_id
    ]
    if project_meta.get("active_material_id") == material_id:
        replacement = project_meta["materials"][0]["id"] if project_meta["materials"] else ""
        project_meta["active_material_id"] = replacement

    with open(get_project_meta_path(project_id), "w", encoding="utf-8") as project_file:
        json.dump(project_meta, project_file, ensure_ascii=True, indent=2)

def list_existing_chunks(project_id, material_id=None):
    """Recupera los chunks existentes en disco."""
    chunks_dir = get_project_chunks_dir(project_id, material_id)
    if not os.path.isdir(chunks_dir):
        return []

    chunk_files = [
        os.path.join(chunks_dir, filename)
        for filename in os.listdir(chunks_dir)
        if filename.startswith("chunk_")
    ]
    return sorted(chunk_files)
