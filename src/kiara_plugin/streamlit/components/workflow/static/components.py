# -*- coding: utf-8 -*-
import uuid
from typing import TYPE_CHECKING, Dict, List, TypeVar, Union

from pydantic import Field

from kiara.api import ValueMap
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.workflow.static import WorkflowSessionStatic

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class StaticWorkflowOptions(ComponentOptions):

    session: WorkflowSessionStatic = Field(description="The current workflow session.")


STATIC_WORKFLOW_OPTIONS_TYPE = TypeVar(
    "STATIC_WORKFLOW_OPTIONS_TYPE", bound=StaticWorkflowOptions
)


class StaticWorkflowComponent(KiaraComponent[STATIC_WORKFLOW_OPTIONS_TYPE]):

    _options = StaticWorkflowOptions  # type: ignore


class StageOutputsPreviewOptions(StaticWorkflowOptions):

    stage_idx: List[int] = Field(
        description="The index of the stage(s) to preview the outputs for."
    )


class PreviousOutputsPreview(StaticWorkflowComponent):

    _component_name = "stage_outputs_preview"
    _options = StageOutputsPreviewOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: StageOutputsPreviewOptions
    ) -> Union[ValueMap, None]:

        session = options.session
        workflow = session.workflow
        pipeline_structure = workflow.pipeline.structure

        current_step_outputs: Dict[str, Dict[str, uuid.UUID]] = {}
        for stage_idx in options.stage_idx:

            stage = pipeline_structure.processing_stages[stage_idx - 1]

            for step in stage:
                for field, value_id in workflow.pipeline.get_current_step_outputs(
                    step
                ).items():
                    current_step_outputs.setdefault(step, {})[field] = value_id

        comp = self.get_component("value_map_preview")

        step_names = list(current_step_outputs.keys())
        tabs = st.tabs(step_names)

        for idx, step in enumerate(step_names):
            values = current_step_outputs[step]
            with tabs[idx]:
                value_map: Union[ValueMap, None] = comp.render_func(st)(
                    value_map=values,
                    add_value_types=True,
                    key=options.create_key("preview", "previous_stages_outputs", step),
                )

        return value_map
