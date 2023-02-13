# -*- coding: utf-8 -*-
import streamlit as st
from kiara.api import KiaraAPI

import kiara_plugin.streamlit as kst
from kiara_plugin.streamlit.modules import DummyModuleConfig

kst.init()

st.write("Kiara example")

api: KiaraAPI = st.kiara.api

data_types = api.list_data_type_names()
st.selectbox("Select data type", data_types, key="data_type")

ops = api.list_operation_ids()
op = st.selectbox("Select operations", ops, key="ops")
st.kiara.item_info(op)

req1 = st.kiara.step_requirements(key="req1")
req2 = st.kiara.step_requirements(key="req2")

create = st.button("Create workflow")
if create:
    pc = DummyModuleConfig.create_pipeline_config(req1, req2)
    st.kiara.pipeline_graph(pc)
