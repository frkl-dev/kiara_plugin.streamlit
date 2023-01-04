# -*- coding: utf-8 -*-
import streamlit as st
from kiara import Value

from kiara_plugin.streamlit.components.workflow.dynamic import WorkflowSession

st.set_page_config(layout="wide")

import kiara_plugin.streamlit as kst

kst.init()

left, right = st.columns((1, 4))
with left:
    init_value: Value = st.kiara.value_input(
        label="**Select initial value**", preview=False
    )

with right:
    st.write("")
    st.write("")
    with st.expander("Value preview", expanded=False):
        if init_value:
            st.kiara.preview(init_value)
        else:
            st.write("-- no value --")
if not init_value:
    st.write("No value selected.")
    st.stop()

workflow_ref = f"workflow_{init_value.data_type_name}"
if workflow_ref not in st.session_state:
    workflow = st.kiara.api.create_workflow()
    workflow_session: WorkflowSession = WorkflowSession(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session
else:
    workflow_session = st.session_state[workflow_ref]

st.kiara.workflow(workflow_session, init_value=init_value)
