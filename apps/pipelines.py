# -*- coding: utf-8 -*-

import streamlit as st

import kiara_plugin.streamlit as kst
from kiara.interfaces.python_api import KiaraAPI

st.set_page_config(layout="wide")
kst.init()
api: KiaraAPI = st.kiara.api

selected = st.kiara.value_list(data_types="file_bundle")

if not selected:
    st.write("No file bundle selected/available.")
    st.stop()


# api.get_value(selected[0]
