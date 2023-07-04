# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Dict

from kiara.api import ValueSchema
from kiara.exceptions import KiaraException
from kiara.models.module.pipeline import StepStatus
from kiara.models.module.pipeline.structure import PipelineStructure
from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.components.workflow.static.components import (
    StaticWorkflowOptions,
)

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class WorkflowStatic(KiaraComponent[StaticWorkflowOptions]):

    _component_name = "workflow_static"
    _options = StaticWorkflowOptions

    def _render(self, st: "KiaraStreamlitAPI", options: StaticWorkflowOptions):

        session = options.session
        workflow = session.workflow
        pipeline_structure: PipelineStructure = workflow.pipeline.structure
        stages = pipeline_structure.processing_stages

        no_input_stages = []
        # calculate no-input stages
        for stage_idx, stage in enumerate(stages, start=1):
            _inputs: Dict[str, ValueSchema] = {}
            for step in stage:
                inputs = pipeline_structure.get_pipeline_inputs_schema_for_step(step)
                _inputs.update(inputs)
            if not _inputs:
                no_input_stages.append(stage_idx)

        left, center, right = st.columns([1, 6, 1])
        prev_placeholder = left.empty()
        next_placeholder = center.empty()
        indicator_placeholder = right.empty()

        if session.current_stage < 1 or session.current_stage > len(stages):
            raise Exception(f"Invalid stage index '{session.current_stage}'.")

        if session.current_stage > 1:
            stage_idx = session.current_stage - 1
            previous_steps = stages[0:stage_idx]

            all_outputs = {}
            stages_to_preview = list(range(1, session.current_stage))
            for stage in previous_steps:
                for step in stage:
                    outputs = workflow.pipeline.get_current_step_outputs(step)
                    all_outputs.update({f"{step}__{k}": v for k, v in outputs.items()})

            with st.expander("Outputs (previous stages)", expanded=False):
                comp = self.get_component("stage_outputs_preview")
                comp.render_func(st)(
                    session=session,
                    stage_idx=stages_to_preview,
                    key=options.create_key("stage_outputs_preview"),
                )

        current_steps = stages[session.current_stage - 1]

        current_inputs: Dict[str, ValueSchema] = {}
        for step in current_steps:
            inputs = pipeline_structure.get_pipeline_inputs_schema_for_step(step)
            current_inputs.update(inputs)

        comp = self.get_component("inputs_for_fields")
        inputs = comp.render(st, current_inputs, smart_label=False)

        workflow.set_inputs(**inputs)

        # st.write(workflow.current_state.dict())
        # step_states = workflow.current_state.pipeline_info.pipeline_state.step_states
        # ready = True
        # for step in current_steps:
        #     if step_states[step].status != StepStatus.RESULTS_READY:
        #         print(f"NOT READY: {step}")
        #         ready = False
        #         break

        steps_to_process = []
        stages_to_process = [session.current_stage]
        for stage in stages[0 : session.current_stage]:
            steps_to_process.append(stage)

        cur = session.current_stage + 1

        while cur in no_input_stages:
            stages_to_process.append(cur)
            steps_to_process.append(stages[cur - 1])
            cur += 1

        left, center, right = st.columns([1, 1, 6])
        process_button = left.button("Process")
        if process_button:
            with st.spinner("Processing..."):  # type: ignore
                for stage in steps_to_process:
                    print(f"PROCESSING STEPS: {stage}")
                    try:
                        job_ids, errors = session.workflow.process_steps(*stage)
                    except Exception as e:
                        st.error(KiaraException.get_root_details(e))
                        break

                    for _step_id, error in errors.items():
                        st.error(error.error)
                    if errors:
                        break

        step_states = workflow.current_state.pipeline_info.pipeline_state.step_states
        ready = True
        for stage in steps_to_process:
            for step in stage:
                if step_states[step].status != StepStatus.RESULTS_READY:
                    print(f"NOT READY: {step}")
                    ready = False
                    break

        if session.current_stage + 1 <= len(stages):
            next_step_disabled = session.current_stage + 1 > len(stages) or not ready
            next_step_button = center.button("Next step", disabled=next_step_disabled)
            if next_step_button:
                current = options.session.current_stage
                if current + 1 <= len(stages):
                    new_stage = current + 1
                    while new_stage in no_input_stages:
                        new_stage += 1
                    options.session.current_stage = new_stage
                    self._st.experimental_rerun()

        with st.expander("Current stage outputs", expanded=True):

            comp = self.get_component("stage_outputs_preview")
            comp.render_func(st)(
                session=session,
                stage_idx=stages_to_process,
                key=options.create_key("stage_outputs_preview"),
            )

        prev_disabled = session.current_stage - 1 < 1
        next_disabled = session.current_stage + 1 > len(stages)

        prev = prev_placeholder.button("Previous", disabled=prev_disabled)
        next = next_placeholder.button("Next", disabled=next_disabled)

        if prev:
            current = options.session.current_stage
            if current - 1 >= 1:
                new_stage = current - 1
                while new_stage in no_input_stages:
                    new_stage -= 1
                options.session.current_stage = new_stage
                self._st.experimental_rerun()

        elif next:
            current = options.session.current_stage
            if current + 1 <= len(stages):
                new_stage = current + 1
                while new_stage in no_input_stages:
                    new_stage += 1
                options.session.current_stage = new_stage
                self._st.experimental_rerun()

        actual_stage = session.current_stage
        for s in no_input_stages:
            if s < actual_stage:
                actual_stage -= 1
        indicator_placeholder.markdown(
            f"Stage {actual_stage} of {len(stages)-len(no_input_stages)}"
        )
