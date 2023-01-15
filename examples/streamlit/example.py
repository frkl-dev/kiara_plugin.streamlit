# -*- coding: utf-8 -*-
import streamlit as st

import kiara_plugin.streamlit as kst

kst.init()

# result = st.kiara.process_operation("create.database.from.table")
# print(result)

b = st.kiara.input_boolean(default=True)
st.write(b)
