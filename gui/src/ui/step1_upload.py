import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import json
from file_manager import get_path, get_session_dir
import pycaps.video.audio_utils as audio_utils
from pycaps import WhisperAudioTranscriber, GoogleAudioTranscriber
from utils import go_to_step, acquire_lock_slot, handle_unexpected_exception
from config import MAX_VIDEO_SIZE, MAX_VIDEO_DURATION, MAX_CONCURRENT_JOBS, SUPPORTED_LANGUAGES

def get_video_duration(video_path: str) -> float:
    """Gets video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(video_path),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (subprocess.CalledProcessError, FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        st.error(f"Could not analyze video file to get duration. Error: {e}")
        return -1

def setup_google_credentials():
    if "GOOGLE_JSON_CREDENTIALS" not in os.environ:
        return False
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8", dir=get_session_dir()) as temp_file:
        temp_file.write(os.environ["GOOGLE_JSON_CREDENTIALS"])
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
    return True

def get_transcriber_instance(language_key: str):
    """
    Dynamically selects the best available transcriber.
    Prefers Google STT if available, otherwise falls back to Whisper.
    """

    google_lang_code, whisper_lang_code = SUPPORTED_LANGUAGES[language_key]
    try:
        was_set = setup_google_credentials()
        if not was_set:
            raise Exception("Unable to setup google credentials")
        transcriber = GoogleAudioTranscriber(language=google_lang_code)
        transcriber._get_client()
        st.session_state.transcriber_used = "Google Speech-to-Text V1"
        return transcriber
    except Exception as e:
        import traceback
        traceback.print_exc()
        st.warning("Google Speech-to-Text not available, falling back to Whisper. Processing may be slower.")
        st.session_state.transcriber_used = "Whisper (base model)"
        return WhisperAudioTranscriber(model_size="base", language=whisper_lang_code)


def render_step1():
    st.header("Upload Your Video")
    
    if st.session_state.active_jobs >= MAX_CONCURRENT_JOBS:
        st.warning("🚧 All our processing slots are currently busy. Please check back in a few minutes.")
        st.info("Tip: You can also duplicate this space to get your own private and free, full-speed version instantly!")
        st.progress(1.0)
        if st.button("Refresh Status"):
            st.rerun()
        return
    
    st.warning(
        """
        **Heads-up on Transcription Quality:** 
        
        To keep this online demo fast, it uses a basic real-time transcription model. The accuracy might be lower than you'd expect.
        For the highest quality and powerful AI transcription, please use the main `pycaps` tool, which leverages **Whisper**. You can check it out on [GitHub](https://github.com/francozanardi/pycaps).
        """
    )

    st.info(
        """
        **Note on Performance:** 
        
        This is a free, shared demo running on community hardware. If you experience slowdowns or queues, it's because others are using it too!
        For a private, full-speed experience, you can **duplicate this Space for free** on your own Hugging Face account in just one click.
        """
    )
    
    if 'audio_being_analyzed' not in st.session_state:
        st.session_state['audio_being_analyzed'] = False
    
    st.info(f"For this demo, please upload a video shorter than **{MAX_VIDEO_DURATION} seconds**.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            f"Select a video file (max {MAX_VIDEO_SIZE // (1024*1024)}MB)",
            type=["mp4", "mov"],
            key=f"uploader_{st.session_state.session_id}"
        )
    
    with col2:
        selected_language_key = st.selectbox(
            "Select Audio Language",
            options=list(SUPPORTED_LANGUAGES.keys()),
            key="language_selector"
        )

    if not uploaded_file:
        return

    if uploaded_file.size > MAX_VIDEO_SIZE:
        st.error(f"File is too large ({uploaded_file.size / (1024*1024):.1f}MB). Max is {MAX_VIDEO_SIZE // (1024*1024)}MB.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_video_path = tmp_file.name
    
    duration = get_video_duration(temp_video_path)
    if duration < 0:
        os.remove(temp_video_path)
        return
    
    if duration > MAX_VIDEO_DURATION:
        st.error(f"Video is too long ({duration:.1f}s). Max duration for the demo is {MAX_VIDEO_DURATION} seconds.")
        os.remove(temp_video_path)
        return

    # Si todo está bien, mostramos el botón
    if st.button("Start Transcription", type="primary", disabled=st.session_state.audio_being_analyzed):
        lock_file = acquire_lock_slot()
        if not lock_file:
            st.error("Sorry, all slots were taken just now. Please try again.")
            os.remove(temp_video_path)
            st.rerun()
        
        st.session_state.lock_file_path = lock_file
        st.session_state.temp_video_path = temp_video_path
        st.session_state.selected_language = selected_language_key
        st.session_state.audio_being_analyzed = True
        st.rerun()
        
    if st.session_state.audio_being_analyzed:
        try:
            video_path = Path(st.session_state.temp_video_path)
            language_key = st.session_state.selected_language
            transcriber = get_transcriber_instance(language_key)
            
            with st.spinner(f"Transcribing audio with {st.session_state.transcriber_used}... 🎧"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                    audio_path = tmp_audio.name
                
                audio_utils.extract_audio_for_whisper(str(video_path), audio_path)
                document = transcriber.transcribe(audio_path)
                
                st.session_state.transcribed_doc = document.to_dict()
                persisted_path = get_path("input.mp4")
                shutil.copy(video_path, persisted_path)
                st.session_state.video_path = persisted_path
                
                os.remove(video_path)
                os.remove(audio_path)
                del st.session_state.temp_video_path
                del st.session_state.selected_language

                st.session_state.audio_being_analyzed = False
                go_to_step(2)
                st.rerun()
                
        except Exception as e:
            if "temp_video_path" in st.session_state and os.path.exists(st.session_state.temp_video_path):
                os.remove(st.session_state.temp_video_path)
            handle_unexpected_exception(e)
