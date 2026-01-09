import streamlit as st
from subtitle_editor import subtitle_editor
from utils import go_to_step, handle_unexpected_exception

def render_step3():
    if not st.session_state.edit_requested:
        go_to_step(4)
        st.rerun()

    st.header("Edit Subtitles")
    st.markdown("Make your changes in the editor below. Clicking 'Save' applies them, while 'Cancel' discards them.")

    editor_result = subtitle_editor(
        initial_document=st.session_state.processed_doc,
        key=f"editor_{st.session_state.session_id}"
    )

    if editor_result is not None:
        try:
            if editor_result.get("action") == "save":
                st.session_state.processed_doc = editor_result.get("document")
                st.toast("✅ Subtitles saved!")
            elif editor_result.get("action") == "cancel":
                st.toast("Editing cancelled. Changes ignored.")
            
            go_to_step(4)
            st.rerun()
        except Exception as e:
            handle_unexpected_exception(e)
