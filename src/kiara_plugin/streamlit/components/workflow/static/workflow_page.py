# -*- coding: utf-8 -*-
from kiara.models.module.pipeline.structure import PipelineStructure
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.components.workflow.static.components import (
    StaticWorkflowOptions,
)


class WorkflowStatic(KiaraComponent[StaticWorkflowOptions]):

    _component_name = "workflow_static"
    _options = StaticWorkflowOptions

    def _render(self, st: DeltaGenerator, options: StaticWorkflowOptions):

        session = options.session
        st.write("STATIC WORKFLOW")
        workflow = session.workflow
        pipeline_structure: PipelineStructure = workflow.pipeline.structure

        stages = pipeline_structure.processing_stages

        if session.current_stage < 1 or session.current_stage >= len(stages):
            raise Exception(f"Invalid stage index '{session.current_stage}'.")

        current_steps = stages[session.current_stage - 1]

        current_inputs = {}
        for step in current_steps:
            inputs = pipeline_structure.get_pipeline_inputs_schema_for_step(step)
            current_inputs.update(inputs)

        comp = self.get_component("input_fields")
        inputs = comp.render(st, current_inputs, smart_label=False)

        workflow.set_inputs(**inputs)

        process_button = st.button("Process")
        if process_button:
            workflow.process_steps(*current_steps)

        current_step_outputs = {}
        for step in current_steps:
            current_step_outputs[step] = workflow.pipeline.get_current_step_outputs(
                step
            )

        st.write(current_step_outputs)
