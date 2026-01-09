import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "template_editor",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)))
)

def template_editor(json, css, key=None):
    component_value = _component_func(
        json=json,
        css=css,
        key=key,
    )
    return component_value
