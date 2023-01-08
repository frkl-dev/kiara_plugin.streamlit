# -*- coding: utf-8 -*-
import streamlit as st

import kiara_plugin.streamlit as kiara_streamlit
from kiara_plugin.streamlit.components.workflow.static import WorkflowSessionStatic

st.set_page_config(layout="wide")

kst = kiara_streamlit.init()

with st.sidebar:
    context_changed = st.kiara.context_switch_control(allow_create=True, key="xxx")

pipeline = "create.network_data.from.files"

workflow_ref = "workflow"
if workflow_ref not in st.session_state or context_changed:
    workflow = st.kiara.api.create_workflow(initial_pipeline=pipeline)
    workflow_session: WorkflowSessionStatic = WorkflowSessionStatic(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session

else:
    workflow_session = st.session_state[workflow_ref]

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

st.kiara.workflow(workflow_session)
