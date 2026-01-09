import streamlit as st
import os
from pycaps import Document
from utils import (go_to_step, reset_all, setup_api_keys, cleanup_api_keys, 
                   handle_unexpected_exception, load_template_files, create_pipeline_builder)
from file_manager import get_random_file_name
from config import TEMPLATE_NAMES, TEMPLATES_INFO
from template_editor import template_editor

def render_step2():
    st.header("Configure & Process")

    if 'editing_mode' not in st.session_state: st.session_state.editing_mode = False
    if 'edited_templates' not in st.session_state: st.session_state.edited_templates = {}

    col1, col2 = st.columns([1, 1])
    with col1:
        render_configuration_column()
    with col2:
        render_preview_column()

def render_configuration_column():
    st.subheader("Configuration")

    if st.session_state.preview_generating:
        return

    if st.session_state.editing_mode:
        handle_editing_mode()
    else:
        handle_preset_selection_mode()

def handle_preset_selection_mode():
    display_names = [
        f"{name} [EDITED]" if (name in st.session_state.edited_templates and st.session_state.edited_templates[name]["modified"]) else name
        for name in TEMPLATE_NAMES
    ]
    
    current_selection_name = st.session_state.get('selected_template', TEMPLATE_NAMES[0])
    try:
        current_index = TEMPLATE_NAMES.index(current_selection_name)
    except ValueError:
        current_index = 0

    selected_display_name = st.selectbox(
        "Choose a Style", display_names, index=current_index
    )
    
    # Extraer el nombre real de la template
    template_name = selected_display_name.replace(" [EDITED]", "")
    st.session_state.selected_template = template_name
    
    selected_template_info = next((t for t in TEMPLATES_INFO if t["name"] == template_name), None)

    if selected_template_info and selected_template_info["ai_features"]:
        ai_features_str = ", ".join(selected_template_info["ai_features"])
        if not st.session_state.get('api_key_input'):
            st.warning(f"⚠️ This template uses AI features ({ai_features_str}). "
                       "Please provide an API key in the sidebar to enable them. "
                       "Otherwise, they will be ignored during processing.")
        else:
            st.info(f"✨ This template uses AI features: {ai_features_str}.")

    st.write("")
    if st.button("✍️ Customize template", use_container_width=True):
        st.session_state.editing_mode = True
        # Si la template no ha sido editada antes, la cargamos desde los archivos originales
        if template_name not in st.session_state.edited_templates:
            initial_data = load_template_files(template_name)
            st.session_state.edited_templates[template_name] = {
                "json": initial_data["json"],
                "css": initial_data["css"],
                "resources_zip": None,
                "modified": False
            }
        st.rerun()
    
    st.divider()
    
    st.session_state.edit_requested = st.checkbox(
        "I want to review and edit the processed subtitles before rendering", 
        value=st.session_state.get('edit_requested', False)
    )
    
    b_next_col, b_back_col = st.columns(2)
    with b_next_col:
        if st.button("Render Video ➡️", type="primary", use_container_width=True):
            process_and_advance()
    with b_back_col:
        if st.button("⬅️ Start Over", use_container_width=True):
            reset_all()
            st.rerun()

def handle_editing_mode():
    template_name = st.session_state.selected_template
    st.info(f"You are customizing the **'{template_name}'** template.")

    current_edit_data = st.session_state.edited_templates[template_name]
    editor_result = template_editor(
        json=current_edit_data["json"],
        css=current_edit_data["css"],
        key=f"editor_{template_name}"
    )

    if editor_result:
        if editor_result.get("action") == "save":
            old_json = st.session_state.edited_templates[template_name].get("json", None)
            old_css = st.session_state.edited_templates[template_name].get("css", None)
            new_json = editor_result["json_content"]
            new_css = editor_result["css_content"]
            # This is a little bit tricky, but this logic can be executed multiple times for the same preview (because of using st.rerun)
            # So, if `was_content_modified` is not used, we are going to remove the preview when this is re-rendered but the code was not changed
            # On the other hand, modified must be always "True", since if we use `was_content_modified` here, it will be "False" when this is re-rendered for the same saving  
            was_content_modified = old_json != new_json or old_css != new_css
            st.session_state.edited_templates[template_name]["json"] = new_json
            st.session_state.edited_templates[template_name]["css"] = new_css
            st.session_state.edited_templates[template_name]["modified"] = True
            if template_name in st.session_state.previews and was_content_modified:
                del st.session_state.previews[template_name]
            st.toast("✅ Template saved!")
            st.success("✅ Template saved!")
        elif editor_result.get("action") == "error":
            st.error(editor_result.get("message", "An error occurred in the editor."))

    st.session_state.edited_templates[template_name]["resources_zip"] = st.file_uploader(
        "(Optional) Upload a `.zip` to add or overwrite resources", type=["zip"],
        key=f"uploader_{template_name}"
    )
    
    edit_buttons_col1, edit_buttons_col2 = st.columns(2)
    with edit_buttons_col1:
        if st.button("Back to Templates", use_container_width=True):
            st.session_state.editing_mode = False
            st.rerun()
    with edit_buttons_col2:
        if st.button("Reset to Original", help="Discards all edits for this template.", use_container_width=True):
            if template_name in st.session_state.edited_templates:
                del st.session_state.edited_templates[template_name]
            if template_name in st.session_state.previews:
                del st.session_state.previews[template_name]
            st.toast(f"Template '{template_name}' has been reset to its original state.")
            st.success(f"Template '{template_name}' has been reset to its original state.")
            st.session_state.editing_mode = False
            st.rerun()

def process_and_advance():
    with st.spinner("Applying configuration..."):
        try:
            builder = create_pipeline_builder()
            builder.with_input_video(st.session_state.video_path)
            setup_api_keys(st.session_state.api_key_type, st.session_state.api_key_input)
            
            pipeline = builder.build()
            pipeline.prepare()
            document = Document.from_dict(st.session_state.transcribed_doc)
            processed_document = pipeline.process_document(document)
            pipeline.close()
            
            st.session_state.processed_doc = processed_document.to_dict()
            go_to_step(3)
            st.rerun()

        except Exception as e:
            handle_unexpected_exception(e)
        finally:
            cleanup_api_keys()

def render_preview_column():
    st.subheader("Live Preview")
    st.markdown("Generate a short, low-quality video preview with the selected style. This takes a few seconds.")
    st.warning("AI features (auto-emojis, ai tagger) are ignored in the preview.")

    preview_container = st.container()
    template_name = st.session_state.get('selected_template')
    
    has_preview_for_template = template_name in st.session_state.previews
    should_disable_button = has_preview_for_template or st.session_state.preview_generating

    if has_preview_for_template:
        preview_container.video(st.session_state.previews[template_name])
    
    if st.button("Generate Preview ⚡", use_container_width=True, disabled=should_disable_button):
        st.session_state.preview_generating = True
        st.rerun()
        
    if st.session_state.preview_generating:
        try:
            with st.spinner("Generating preview video... ⚡"):
                builder = create_pipeline_builder()
                builder.with_input_video(st.session_state.video_path)
                pipeline = builder.build(preview_time=(0, 5))
                document = Document.from_dict(st.session_state.transcribed_doc)
                
                pipeline.prepare()
                processed_document = pipeline.process_document(document)
                pipeline.render(processed_document)
                pipeline.close()

                preview_output_path = pipeline._output_video_path
                if preview_output_path and os.path.exists(preview_output_path):
                    st.session_state.previews[template_name] = preview_output_path
                else:
                    raise RuntimeError("Could not generate preview.")
        except Exception as e:
            handle_unexpected_exception(e)
        finally:
            st.session_state.preview_generating = False
            st.rerun()
    