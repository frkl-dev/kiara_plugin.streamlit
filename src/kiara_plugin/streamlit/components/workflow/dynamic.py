# -*- coding: utf-8 -*-
from kiara_plugin.streamlit import KiaraStreamlit
from kiara_plugin.streamlit.components import KiaraComponent


class DynamicWorkflow(KiaraComponent):
    def __init__(self, kiara_streamlit: KiaraStreamlit):

        super().__init__(kiara_streamlit)
