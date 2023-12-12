# -*- coding: utf-8 -*-


import kiara_plugin.streamlit as kst
from kiara.interfaces.python_api import KiaraAPI

st = kst.init(page_config={"layout": "wide"})

api: KiaraAPI = st.kiara
api.kiara_api_help()
