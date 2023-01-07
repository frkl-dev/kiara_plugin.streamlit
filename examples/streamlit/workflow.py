# -*- coding: utf-8 -*-
import streamlit as st

import kiara_plugin.streamlit as kiara_streamlit
from kiara_plugin.streamlit.components.workflow.dynamic import DynamicWorkflowSession

st.set_page_config(layout="wide")

kst = kiara_streamlit.init()

with st.sidebar:
    context_changed = st.kiara.context_switch_control(allow_create=True, key="xxx")

if not st.kiara.api.get_alias_names():
    with st.spinner("Downloading example data ..."):

        result = st.kiara.api.run_job(
            operation="download.file",
            inputs={
                "url": "https://github.com/DHARPA-Project/kiara.examples/raw/main/examples/data/journals/JournalNodes1902.csv"
            },
        )
        st.kiara.api.store_value(value=result["file"], alias="journal_nodes_file")

        result = st.kiara.api.run_job(
            operation="download.file",
            inputs={
                "url": "https://github.com/DHARPA-Project/kiara.examples/raw/main/examples/data/journals/JournalEdges1902.csv"
            },
        )
        st.kiara.api.store_value(value=result["file"], alias="journal_edges_file")

workflow_ref = "workflow"
if workflow_ref not in st.session_state or context_changed:
    workflow = st.kiara.api.create_workflow()
    workflow_session: DynamicWorkflowSession = DynamicWorkflowSession(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session
    # st.experimental_rerun()
else:
    workflow_session = st.session_state[workflow_ref]

st.kiara.workflow(workflow_session)
