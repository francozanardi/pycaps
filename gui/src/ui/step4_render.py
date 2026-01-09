import streamlit as st
import os
from pycaps import Document
from utils import go_to_step, create_pipeline_builder, setup_api_keys, handle_unexpected_exception

def render_step4():
    st.header("Final Render")
    api_key = st.session_state.get('api_key_input')
    api_key_type = st.session_state.get('api_key_type')
    
    try:
        with st.spinner("Rendering final video... This is the last step! 🎬"):
            pipeline = create_pipeline_builder().with_input_video(st.session_state.video_path).build()
            if not pipeline:
                raise RuntimeError("Could not build pipeline for rendering.")
            
            setup_api_keys(api_key_type, api_key)
            pipeline.prepare()
            document_to_render = Document.from_dict(st.session_state.processed_doc)
            pipeline.render(document_to_render)
            
            if pipeline._output_video_path and os.path.exists(pipeline._output_video_path):
                st.session_state.final_video_path = pipeline._output_video_path
                go_to_step(5)
                st.rerun()
            else:
                st.error("Render failed. Check the logs.")
    except Exception as e:
        handle_unexpected_exception(e)
