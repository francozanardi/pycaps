import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "subtitle_editor",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)))
)

def subtitle_editor(initial_document, key=None):
    component_value = _component_func(
        initial_document=initial_document,
        key=key,
    )
    return component_value