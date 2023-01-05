# -*- coding: utf-8 -*-
# import streamlit as st
#
# from kiara_plugin.streamlit.components.workflow.dynamic import WorkflowSession
#
# st.set_page_config(layout="wide")
#
# import kiara_plugin.streamlit as kst
#
# kst.init()
#
# workflow_ref = f"workflow"
# if workflow_ref not in st.session_state:
#     workflow = st.kiara.api.create_workflow()
#     workflow_session: WorkflowSession = WorkflowSession(workflow=workflow)
#     st.session_state[workflow_ref] = workflow_session
# else:
#     workflow_session = st.session_state[workflow_ref]
#
# st.kiara.workflow(workflow_session)
