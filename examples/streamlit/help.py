# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(layout="wide")

import kiara_plugin.streamlit as kst

kst.init()

# st.kiara.data_type_info()
# st.kiara.operation_info()
# st.kiara.module_type_info()
# st.kiara.kiara_api_help()
st.kiara.kiara_component_help()