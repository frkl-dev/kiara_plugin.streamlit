# -*- coding: utf-8 -*-

import streamlit as st

import kiara_plugin.streamlit as kst

kst.init()

# result = st.kiara.process_operation("create.database.from.table")
# print(result)


st.kiara.pipeline_graph("logic.xor")
