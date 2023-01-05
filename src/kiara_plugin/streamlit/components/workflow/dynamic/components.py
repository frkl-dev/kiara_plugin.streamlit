# -*- coding: utf-8 -*-
from typing import Dict, Tuple, TypeVar

from kiara import Value
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.workflow.dynamic import DynamicWorkflowSession


class DynamicWorkflowOptions(ComponentOptions):

    session: DynamicWorkflowSession = Field(description="The current workflow session.")


DYN_WORKFLOW_OPTIONS_TYPE = TypeVar(
    "DYN_WORKFLOW_OPTIONS_TYPE", bound=DynamicWorkflowOptions
)


class DynamicWorkflowComponent(KiaraComponent[DYN_WORKFLOW_OPTIONS_TYPE]):

    _component_name = "dynamic_workflow"
    _options = DynamicWorkflowOptions  # type: ignore


class StepDetailsOptions(DynamicWorkflowOptions):

    step_id: str = Field(description="The id of the step to show details for.")


class WriteStepComponent(DynamicWorkflowComponent):

    _component_name = "write_step_details"
    _options = StepDetailsOptions  # type: ignore

    def _render(self, st: DeltaGenerator, options: StepDetailsOptions):

        idx = options.session.pipeline_steps.index(options.step_id)

        st.markdown("### Inputs")
        for field, value in options.session.values[idx].items():
            st.markdown(f"#### Input: **{field}**")
            # _key = options.create_key("input", "preview", field)
            # self.kiara_streamlit.preview(key=_key, value=value)
            comp = self.get_component("preview")
            _key = options.create_key("input", "value", field)
            comp.render_func(st)(key=_key, value=value)


class NextStepOptions(DynamicWorkflowOptions):

    value: Value = Field(description="The value to use for the next step.")
    columns: Tuple[int, int] = Field(
        description="The column layout to use for the next step.", default=(1, 4)
    )


class NextStepComponent(DynamicWorkflowComponent):

    _component_name = "ask_next_step"
    _options = NextStepOptions

    def _render(self, st: DeltaGenerator, options: NextStepOptions):

        value = options.value

        left, right = st.columns(options.columns)

        operations = self.api.get_operations_info(input_types=value.data_type_name)
        all_tags = set()
        for op in operations.item_infos.values():
            all_tags.update(op.context.tags)

        left.markdown("**Select next step**")
        expander = left.expander("Filter operations", expanded=False)
        with expander:
            selected_tags = st.multiselect(
                label="Tags", options=all_tags, key=options.create_key("tags")
            )

        if selected_tags:
            ops = []

            for op_id, op in operations.item_infos.items():
                match = True
                for tag in selected_tags:
                    if tag not in op.context.tags:
                        match = False
                        break
                if match:
                    ops.append(op_id)
        else:
            ops = operations.item_infos.keys()

        selected = left.selectbox(
            label="Operation",
            options=sorted(ops),
            key=options.create_key("operation_select"),
        )
        if selected:
            right.write("")
            right.write("")
            with right:
                with st.expander("Operation details", expanded=False):
                    st.kiara.operation_info(operation_id=selected)
            left.write(operations[selected].documentation.description)
            return operations[selected]
        else:
            return None


class StepInputFields(DynamicWorkflowComponent):

    _component_name = "step_input_fields"
    _options = StepDetailsOptions

    def _render(
        self, st: DeltaGenerator, options: StepDetailsOptions
    ) -> Dict[str, Value]:

        step_id = options.step_id
        idx = options.session.pipeline_steps.index(step_id)
        workflow = options.session.workflow

        fixed_input = options.session.values[idx]
        field_name = next(iter(fixed_input.keys()))
        value = fixed_input[field_name]

        missing_fields = {}
        for _f, schema in workflow.get_current_inputs_schema_for_step(step_id).items():
            if _f == field_name:
                continue
            missing_fields[_f] = schema

        step = workflow.get_step(step_id)
        _key = options.create_key("missing_inputs_step", step.step_id)

        with st.expander(label="Provide missing operation inputs", expanded=True):
            if not missing_fields:
                st.write("No additional inputs necessary.")
                new_inputs = {}
            else:
                comp = self.kiara_streamlit.get_component("input_fields")
                _key = options.create_key("missing_inputs_fields", step.step_id)
                new_inputs = comp.render_func(st)(key=_key, fields=missing_fields)

        assert field_name not in new_inputs
        result = {field_name: value}
        for k, v in new_inputs.items():
            result[k] = v

        return result
