# -*- coding: utf-8 -*-
import os

import kiara_plugin.streamlit as kst
from kiara.interfaces.python_api import JobDesc

st = kst.init(page_config={"layout": "wide"})

st.kiara.api.set_active_context("components_doc", create=True)

if "file_bundle" not in st.kiara.api.list_alias_names():

    with st.spinner("Downloading example data ..."):
        job_file = os.path.join(
            os.path.dirname(__file__), "jobs", "download_journals.yaml"
        )
        job_desc = JobDesc.create_from_file(path=job_file)

        results = st.kiara.api.run_job(job_desc)

        for field_name, value in results.items():
            st.kiara.api.store_value(value, field_name)


st.kiara.component_info()
