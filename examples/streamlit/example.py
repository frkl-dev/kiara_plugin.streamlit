# -*- coding: utf-8 -*-
import streamlit as st

import kiara_plugin.streamlit as kst

st.set_page_config(layout="wide")
kst.init()

# st.kiara.value_input(data_types="table", preview="checkbox")
#
# inp = st.kiara.input_integer(style="text_input")
# if inp:
#     st.write(inp.data)

op_inputs = st.kiara.operation_inputs("table.cut_column")
# op_inputs: ValueMap = st.kiara.operation_inputs("preprocess.tokens_array")
# for k, v in op_inputs.get_all_value_data().items():
#     st.write("-----")
#     st.write(k)
#     st.write(v)

# str_input = st.kiara.string_input()
# print(str_input)
# st.write(str_input.data)
# st.kiara.preview(value="corpus")
#
# st.kiara.value_list_preview()
# st.kiara.kiara_api_help()
# st.kiara.kiara_component_help()
