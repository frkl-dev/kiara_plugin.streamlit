# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, List, Literal, Union

import networkx as nx
from pydantic import ConfigDict, Field

from kiara.interfaces.python_api import OperationInfo
from kiara.models.module.operation import Operation
from kiara.models.module.pipeline import PipelineConfig
from kiara.models.module.pipeline.structure import PipelineStructure
from kiara_plugin.streamlit.components import (
    ComponentOptions,
    KiaraComponent,
)

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class PipelineSelectOptions(ComponentOptions):
    filters: List[str] = Field(
        description="Filter tokens that must be present in the pipeline/operation name.",
        default_factory=list,
    )


class PipelineSelect(KiaraComponent[PipelineSelectOptions]):

    _component_name = "select_pipeline"
    _options = PipelineSelectOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: PipelineSelectOptions
    ) -> Union[None, OperationInfo]:

        pipeline_infos = self.api.retrieve_operations_info(
            *options.filters, operation_types=["pipeline"]
        )

        op_ids = list(pipeline_infos.item_infos.keys())
        result = st.selectbox("Select pipeline", options=op_ids)
        if result:
            return pipeline_infos.item_infos[result]
        else:
            return None


class PipelineGraphOptions(ComponentOptions):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph_type: Literal[
        "execution", "data_flow", "data_flow_simple", "user_select"
    ] = Field(description="The type of graph to display.", default="user_select")
    pipeline: Union[
        str, Operation, OperationInfo, PipelineConfig, PipelineStructure
    ] = Field(description="The pipeline to display.")


class PipelineGraph(KiaraComponent[PipelineGraphOptions]):
    """Display the structure of a pipeline as a graph."""

    _component_name = "pipeline_graph"
    _options = PipelineGraphOptions
    _examples = [
        {
            "doc": "Display the execution graph of the 'logic.xor' pipeline.",
            "args": {
                "pipeline": "logic.xor",
                "graph_type": "execution",
            },
        }
    ]

    def _render(self, st: "KiaraStreamlitAPI", options: PipelineGraphOptions) -> None:

        if isinstance(options.pipeline, str):
            op: Operation = self.api.get_operation(options.pipeline)
            structure = op.pipeline_config.structure
        elif isinstance(options.pipeline, OperationInfo):
            structure = options.pipeline.operation.pipeline_config.structure
        elif isinstance(options.pipeline, Operation):
            structure = options.pipeline.pipeline_config.structure
        elif isinstance(options.pipeline, PipelineConfig):
            structure = options.pipeline.structure
        elif isinstance(options.pipeline, PipelineStructure):
            structure = options.pipeline
        else:
            raise Exception(f"Invalid type for pipeline: {type(options.pipeline)}.")

        graph_type = options.graph_type
        if graph_type == "user_select":
            graph_type = st.radio(
                "Select graph type",
                ["execution", "data_flow_simple", "data_flow"],
                index=0,
                horizontal=True,
            )

        if graph_type == "execution":
            graph = structure.execution_graph
        elif graph_type == "data_flow":
            graph = structure.data_flow_graph
        elif graph_type == "data_flow_simple":
            graph = structure.data_flow_graph_simple
        else:
            raise Exception("Invalid graph type: {options.graph_type}")

        def rename_node(node):
            return f'"{str(node)}"'  # noqa

        mapping = {node: rename_node(node) for node in graph.nodes()}
        graph = graph.copy()
        nx.relabel_nodes(graph, mapping, copy=False)

        dot = nx.nx_pydot.to_pydot(graph)
        st.graphviz_chart(dot.to_string())


# class PipelineInfoPanelConfig(ComponentOptions):
#
#     pipeline: Union[str, Operation, OperationInfo, PipelineConfig, PipelineStructure] = Field(
#         description="The pipeline to display."
#     )
# class PipelineInfoPanel(KiaraComponent[PipelineInfoPanelConfig]):
#
#     _component_name = "pipeline_info"
#     _options = PipelineInfoPanelConfig
#     _examples = []
#
#     def _render(self, st: "KiaraStreamlitAPI", options: PipelineInfoPanelConfig) -> None:
#
#         if isinstance(options.pipeline, str):
#             op: Operation = self.api.get_operation(options.pipeline)
#             structure = op.pipeline_config.structure
#         elif isinstance(options.pipeline, OperationInfo):
#             structure = options.pipeline.operation.pipeline_config.structure
#         elif isinstance(options.pipeline, Operation):
#             structure = options.pipeline.pipeline_config.structure
#         elif isinstance(options.pipeline, PipelineConfig):
#             structure = options.pipeline.structure
#         elif isinstance(options.pipeline, PipelineStructure):
#             structure = options.pipeline
#         else:
#             raise Exception(f"Invalid type for pipeline: {type(options.pipeline)}.")
#
#         st.write("xxx")
#         st.write(structure.model_dump())
