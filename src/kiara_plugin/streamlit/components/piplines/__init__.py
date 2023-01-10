# -*- coding: utf-8 -*-
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent


class PipelineSelect(KiaraComponent):

    _component_name = "select_pipeline"

    def _render(self, st: DeltaGenerator, options: ComponentOptions):

        pipeline_infos = self.api.get_operations_info(operation_types=["pipeline"])

        op_ids = list(pipeline_infos.item_infos.keys())
        result = st.selectbox("Select pipeline", options=op_ids)

        return result
