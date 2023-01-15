# -*- coding: utf-8 -*-
from typing import List

from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent


class PipelineSelectOptions(ComponentOptions):
    filters: List[str] = Field(
        description="Filter tokens that must be present in the pipeline/operation name.",
        default_factory=list,
    )


class PipelineSelect(KiaraComponent[PipelineSelectOptions]):

    _component_name = "select_pipeline"
    _options = PipelineSelectOptions

    def _render(self, st: DeltaGenerator, options: PipelineSelectOptions):

        pipeline_infos = self.api.retrieve_operations_info(
            *options.filters, operation_types=["pipeline"]
        )

        op_ids = list(pipeline_infos.item_infos.keys())
        result = st.selectbox("Select pipeline", options=op_ids)

        return result
