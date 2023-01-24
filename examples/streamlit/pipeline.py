# -*- coding: utf-8 -*-

import nltk
import streamlit as st

import kiara_plugin.streamlit as kiara_streamlit
from kiara_plugin.streamlit.components.workflow.static import WorkflowSessionStatic

st.set_page_config(layout="wide")

nltk.download("punkt")
nltk.download("stopwords")

kst = kiara_streamlit.init()

current = kst.api.get_current_context_name()
with st.sidebar:
    selected_context = st.kiara.context_switch_control(allow_create=True, key="xxx")
    context_changed = current != selected_context

pipeline = {
    "pipeline_name": "logic.nor",
    "doc": "Returns 'True' if both inputs are 'False'.",
    "steps": [
        {"module_type": "logic.or", "step_id": "or"},
        {"module_type": "logic.not", "step_id": "not", "input_links": {"a": "or.y"}},
    ],
    "input_aliases": {"or.a": "a", "or.b": "b"},
    "output_aliases": {"not.y": "y"},
}


workflow_ref = "workflow_static"
if workflow_ref not in st.session_state or context_changed:
    workflow = st.kiara.api.create_workflow(initial_pipeline=pipeline)
    workflow_session: WorkflowSessionStatic = WorkflowSessionStatic(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session

else:
    workflow_session = st.session_state[workflow_ref]

st.kiara.workflow(workflow_session)
