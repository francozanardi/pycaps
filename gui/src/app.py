import streamlit as st
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
import logging
from pycaps import logger

from utils import initialize_session_state, reset_all, get_queue_status
from ui.sidebar import render_sidebar
from ui.step1_upload import render_step1
from ui.step2_configure import render_step2
from ui.step3_edit import render_step3
from ui.step4_render import render_step4
from ui.step5_view import render_step5
from file_manager import init_file_manager

st.set_page_config(layout="wide", page_title="Pycaps Demo")
logger.set_logging_level(logging.DEBUG)
initialize_session_state()
init_file_manager()

# --- Renderizado de la UI ---
st.title("🎬 Pycaps Demo")
st.markdown("""
<style>
.stElementContainer > video {
  max-height: 50vh;
}
</style>
""", unsafe_allow_html=True)

render_sidebar()

step_router = {
    1: render_step1,
    2: render_step2,
    3: render_step3,
    4: render_step4,
    5: render_step5,
}

if st.session_state.error_message:
    st.error(st.session_state.error_message)
    st.warning("Your session has been reset due to an error. Please try again.")
    if st.button("🏠 Start Over"):
        reset_all()
        st.rerun()
else:
    current_step = st.session_state.current_step
    render_function = step_router.get(current_step)

    if render_function:
        st.session_state.active_jobs = get_queue_status()
        render_function()
    else:
        st.error("Invalid step. Resetting application.")
        reset_all()
        st.rerun()
