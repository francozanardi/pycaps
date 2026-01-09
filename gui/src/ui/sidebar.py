import streamlit as st
from utils import get_queue_status
from config import MAX_CONCURRENT_JOBS

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ API Configuration")
        st.info(
            "API keys are optional and only required for AI features "
            "like **Auto-Emoji** or **AI Tagger**."
        )
        st.radio("Select API Key Type", ("Pycaps API (Recommended)", "OpenAI API"), key="api_key_type")
        st.text_input("Enter your API Key", type="password", key="api_key_input")
        
        st.markdown("---")
        
        st.header("📊 Job Status")
        active_jobs = get_queue_status()
        st.metric(
            label="Concurrent Jobs Running",
            value=f"{active_jobs} / {MAX_CONCURRENT_JOBS}"
        )

        st.markdown("---")

        st.header("About Pycaps")
        st.markdown(
            "**Pycaps** is an open-source tool for adding stylish, "
            "animated subtitles to videos."
        )
        st.markdown(
            "[⭐ Star on GitHub](https://github.com/francozanardi/pycaps)"
        )
        st.markdown(
            "[📄 Read the Docs](https://github.com/francozanardi/pycaps/blob/main/README.md)"
        )
