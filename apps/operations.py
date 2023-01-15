# -*- coding: utf-8 -*-
import os

import streamlit as st

import kiara_plugin.streamlit as kst

st.set_page_config(layout="wide")

kst.init()
st.kiara.api.set_active_context("_operation_doc", create=True)

if "corpus_files" not in st.kiara.api.list_alias_names():
    with st.spinner("Downloading example data ..."):
        pipeline_file = os.path.join(
            os.path.dirname(__file__), "pipelines", "operations_doc_onboarding.yaml"
        )
        results = st.kiara.api.run_job(pipeline_file)

        for field_name, value in results.items():
            st.kiara.api.store_value(value, field_name)

st.kiara.operation_documentation()
