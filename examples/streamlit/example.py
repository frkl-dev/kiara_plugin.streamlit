# -*- coding: utf-8 -*-
import streamlit as st

import kiara_plugin.streamlit as kiara_streamlit

st.set_page_config(layout="wide")

kst = kiara_streamlit.init()

# st.kiara.context_switch_control(allow_create=True)
st.kiara.context_switch_control(allow_create=False)

# dbg(dict(st.session_state))
# # create_modal = Modal("Create new context", key="create_context_modal")
# #
# # if create_button:
# #     create_modal.open()
# #
# # context_created = False
# # if create_modal.is_open():
# #     with create_modal.container():
# #         new_context_name = st.text_input(label="Context name")
# #         create_context_button = st.button("Create", disabled=not new_context_name)
# #         if create_context_button:
# #             kst.api.create_new_context(new_context_name, set_active=True)
# #             context_created = True
# #             create_modal.close()
# # if context_created:
# #     st.experimental_rerun()
#
# if context_name != current:
#     kst.api.set_active_context(context_name)
#
st.write(kst.api.list_aliases())
