# -*- coding: utf-8 -*-

import streamlit as st

import kiara_plugin.streamlit as kiara_streamlit

st.set_page_config(layout="wide")

kst = kiara_streamlit.init()

st.kiara.operation_info()
