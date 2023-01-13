# -*- coding: utf-8 -*-

import streamlit as st

import kiara_plugin.streamlit as kst

st.set_page_config(layout="wide")

kst.init()

st.kiara.operation_documentation()
