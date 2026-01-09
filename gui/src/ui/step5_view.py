import streamlit as st
from utils import go_to_step, reset_all, release_lock_slot_if_needed, acquire_lock_slot, display_video

def render_step5():
    st.header("Your Video is Ready!")

    release_lock_slot_if_needed()

    if 'final_video_path' in st.session_state and st.session_state.final_video_path:
        display_video(st.session_state.final_video_path)
    else:
        st.error("Could not find the final video.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Choose Another Style", use_container_width=True):
            lock_file = acquire_lock_slot()
            if not lock_file:
                st.warning("🚧 All our processing slots are currently busy. Please check back in a few minutes.")
            else:
                st.session_state.lock_file_path = lock_file
                keys_to_delete = ['processed_doc', 'final_video_path', 'edit_requested']
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                go_to_step(2)
                st.rerun()

    with col2:
        if st.button("🏠 Start with a New Video", use_container_width=True):
            reset_all()
            st.rerun()
