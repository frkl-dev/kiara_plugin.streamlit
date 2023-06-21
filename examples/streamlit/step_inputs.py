# -*- coding: utf-8 -*-

import streamlit as st

st.set_page_config(layout="wide")

if "steps" in st.session_state.keys():
    steps = st.session_state["steps"]
else:
    steps = {}
    st.session_state["steps"] = steps

for idx, step in steps.items():
    title = step["title"]
    desc = step["desc"]
    st.write(f"Step {idx}")
    steps[idx]["title"] = st.text_input("Title", value=title, key=f"title_step_{idx}")
    steps[idx]["desc"] = st.text_area("Description", value=desc, key=f"desc_step_{idx}")

add_step = st.button("Add step")
if add_step:
    new_step_id = len(steps.keys())
    steps[new_step_id] = {"title": "<the step title>", "desc": "<the step description>"}
    st.experimental_rerun()

st.write(steps)
