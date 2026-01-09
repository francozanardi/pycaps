import streamlit as st
import os
import time
import glob
import uuid
from pathlib import Path
import importlib.resources as resources
from importlib.abc import Traversable
import zipfile
import json
import shutil
from pathlib import Path
from file_manager import create_temp_dir, get_random_file_name

from pycaps.api import ApiKeyService
from pycaps import TemplateLoader, JsonConfigLoader
from config import LOCK_DIR, LOCK_TTL_SECONDS, MAX_CONCURRENT_JOBS

# --- Lock Management ---

def release_lock_slot(lock_file_path):
    if lock_file_path and os.path.exists(lock_file_path):
        try:
            os.remove(lock_file_path)
        except OSError:
            pass

def cleanup_stale_locks():
    for lock_file in glob.glob(os.path.join(LOCK_DIR, "*.lock")):
        try:
            timestamp_str = Path(lock_file).stem.split('_')[0]
            creation_time = float(timestamp_str)
            if time.time() - creation_time > LOCK_TTL_SECONDS:
                release_lock_slot(lock_file)
        except (ValueError, IndexError):
            release_lock_slot(lock_file)

def acquire_lock_slot():
    cleanup_stale_locks()
    current_jobs = len(glob.glob(os.path.join(LOCK_DIR, "*.lock")))
    if current_jobs >= MAX_CONCURRENT_JOBS:
        return None
    
    lock_id = f"{time.time()}_{uuid.uuid4()}"
    lock_file_path = os.path.join(LOCK_DIR, f"{lock_id}.lock")
    with open(lock_file_path, "w") as f:
        f.write(str(os.getpid()))
    return lock_file_path

def get_queue_status():
    cleanup_stale_locks()
    current_jobs = len(glob.glob(os.path.join(LOCK_DIR, "*.lock")))
    return current_jobs

# --- API Key Management ---

def setup_api_keys(key_type: str, key: str):
    if key:
        if key_type == "Pycaps API (Recommended)":
            ApiKeyService.set(key)
        elif key_type == "OpenAI API":
            os.environ["PYCAPS_OPENAI_API_KEY"] = key

def cleanup_api_keys():
    if ApiKeyService.has():
        ApiKeyService.remove()
    if "PYCAPS_OPENAI_API_KEY" in os.environ:
        del os.environ["PYCAPS_OPENAI_API_KEY"]

# --- State Management ---

def go_to_step(step):
    st.session_state.current_step = step

def release_lock_slot_if_needed():
    if st.session_state.lock_file_path:
        release_lock_slot(st.session_state.lock_file_path)
        st.session_state.lock_file_path = None
        
def reset_all():
    release_lock_slot_if_needed()
    persisted_keys = ['api_key_type', 'api_key_input']
    for key in list(st.session_state.keys()):
        if key not in persisted_keys:
            del st.session_state[key]
            
    go_to_step(1)

def initialize_session_state():
    defaults = {
        'current_step': 1,
        'video_path': None,
        'transcribed_doc': None,
        'processed_doc': None,
        'edit_requested': False,
        'final_video_path': None,
        'session_id': str(uuid.uuid4()),
        'selected_template': None,
        'previews': {},
        'preview_generating': False,
        'lock_file_path': None,
        'error_message': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Pipeline & Display ---

def create_pipeline_builder():
    template_name = st.session_state.selected_template
    if template_name not in st.session_state.edited_templates:
        return (
            TemplateLoader(template_name)
            .load(False)
            .should_save_subtitle_data(False)
            .with_output_video(get_random_file_name("mp4"))
        )
    
    edited_data = st.session_state.edited_templates[template_name]
    temp_dir = create_temp_dir()
    original_template_path = get_template_path(template_name)
    resources_dir = Path(temp_dir) / "resources"
    os.makedirs(resources_dir, exist_ok=True)
    
    # Primero, copiar recursos originales si existen
    if original_template_path and (original_template_path / "resources").is_dir():
        edited_data["json"]["resources"] = "resources"
        shutil.copytree(str(original_template_path / "resources"), str(resources_dir), dirs_exist_ok=True)
    
    # Luego, descomprimir y sobrescribir con los recursos subidos por el usuario
    if edited_data.get('resources_zip'):
        edited_data["json"]["resources"] = "resources"
        with zipfile.ZipFile(edited_data['resources_zip'], 'r') as zip_ref:
            zip_ref.extractall(resources_dir)
    
    # Crear los archivos de configuración en el directorio temporal
    config_path = Path(temp_dir) / "pycaps.json"
    with open(config_path, "w") as f:
        edited_data["json"]["css"] = "styles.css"
        json.dump(edited_data["json"], f, indent=2)
    
    css_path = Path(temp_dir) / "styles.css"
    with open(css_path, "w") as f:
        f.write(edited_data["css"])
    
    return (
        JsonConfigLoader(str(config_path))
        .load(False)
        .should_save_subtitle_data(False)
        .with_output_video(get_random_file_name("mp4"))
    )

def handle_unexpected_exception(e):
    st.session_state.error_message = f"Unexpected error: {e}"
    if st.session_state.lock_file_path:
        release_lock_slot(st.session_state.lock_file_path)
    st.session_state.lock_file_path = None
    import traceback
    traceback.print_exc()
    st.rerun()

def display_video(video_path):
    with st.container():
        st.video(video_path)
        with open(video_path, "rb") as file:
            video_bytes = file.read()
        st.download_button(
            "⬇️ Download Video", video_bytes, 
            f"pycaps_{Path(video_path).stem}.mp4", "video/mp4"
        )

def get_template_path(template_name: str) -> Traversable:
    """Obtiene la ruta a la carpeta de una template predefinida."""
    try:
        return resources.files(f"pycaps.template.preset.{template_name}")
    except ModuleNotFoundError:
        return None

def load_template_files(template_name: str) -> dict:
    """Carga el contenido de los archivos de una template predefinida."""
    template_path = get_template_path(template_name)
    if not template_path:
        return {"json": {}, "css": ""}

    try:
        with (template_path / "pycaps.template.json").open("r", encoding="utf-8") as f:
            json_content = json.load(f)
    except FileNotFoundError:
        json_content = {}
    
    try:
        with (template_path / "styles.css").open("r", encoding="utf-8") as f:
            css_content = f.read()
    except FileNotFoundError:
        css_content = ""
        
    return {"json": json_content, "css": css_content}
