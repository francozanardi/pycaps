import os
import shutil
import tempfile
import time
import uuid
import streamlit as st
from config import SESSION_TTL_SECONDS

def init_file_manager():
    base_dir = get_base_sessions_dir()
    os.makedirs(base_dir, exist_ok=True)
    session_dir = get_session_dir()
    os.makedirs(session_dir, exist_ok=True)
    touch()
    cleanup_expired_sessions()

def get_base_sessions_dir():
    return os.path.join(tempfile.gettempdir(), "pycaps-sessions")

def get_session_dir():
    return os.path.join(get_base_sessions_dir(), st.session_state.session_id)

def get_path(*relative_path):
    return os.path.join(get_session_dir(), *relative_path)

def get_random_file_name(ext):
    return get_path(f"{uuid.uuid4()}.{ext}")

def create_temp_file(suffix="", prefix="tmp", text=False):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=get_session_dir(), text=text)
    # Abre y devuelve el archivo como objeto file abierto (similar a NamedTemporaryFile)
    mode = "w+" if text else "w+b"
    file_obj = os.fdopen(fd, mode)
    return file_obj

def create_temp_dir(suffix="", prefix="tmp"):
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=get_session_dir())

def touch():
    keepalive_path = os.path.join(get_session_dir(), ".keepalive")
    with open(keepalive_path, "w") as f:
        f.write(str(time.time()))

def cleanup_expired_sessions():
    now = time.time()
    for name in os.listdir(get_base_sessions_dir()):
        path = os.path.join(get_base_sessions_dir(), name)
        if not os.path.isdir(path):
            continue
        try:
            keepalive_file = os.path.join(path, ".keepalive")
            if os.path.exists(keepalive_file):
                last_touched = os.path.getmtime(keepalive_file)
            else:
                last_touched = os.path.getmtime(path)
            if now - last_touched > SESSION_TTL_SECONDS:
                shutil.rmtree(path)
        except Exception as e:
            pass

def delete_current_session_dir():
    shutil.rmtree(get_session_dir(), ignore_errors=True)
