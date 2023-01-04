# -*- coding: utf-8 -*-
from typing import Dict, List, Mapping, Union

from kiara import Value, ValueSchema
from kiara.interfaces.python_api import OperationInfo, Workflow
from kiara.models.documentation import DocumentationMetadataModel
from kiara.models.module.operation import Operation
from kiara.models.module.pipeline import PipelineStep, generate_pipeline_endpoint_name
from pydantic import BaseModel, Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.defaults import PROFILE_KEYWORD


class WorkflowSession(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    values: Dict[int, Dict[str, Value]] = Field(
        description="The values that are already set for this workflow.",
        default_factory=dict,
    )
    pipeline_steps: List[str] = Field(
        description="The steps that were added to this workflow, in order.",
        default_factory=list,
    )
    workflow: Workflow = Field(description="The workflow instance.")
    last_step_processed: bool = Field(
        description="Whether the last step was valid.", default=False
    )
    last_operation: Union[None, OperationInfo] = Field(
        description="The last operation that was selected.", default=None
    )


class DynamicWorkflow(KiaraComponent):

    _component_name = "workflow"

    def remove_last_step(self, workflow_session: WorkflowSession) -> None:

        if workflow_session.pipeline_steps:
            idx = len(workflow_session.pipeline_steps) - 1
            last_step = workflow_session.pipeline_steps.pop()
            workflow_session.values.pop(idx)
            workflow_session.workflow.clear_steps(last_step)

        workflow_session.last_step_processed = False

    def ask_for_next_step(
        self,
        st: DeltaGenerator,
        left: DeltaGenerator,
        right: DeltaGenerator,
        key: str,
        value: Value,
    ) -> Union[None, OperationInfo]:

        operations = self.api.get_operations_info(input_types=value.data_type_name)
        all_tags = set()
        for op in operations.item_infos.values():
            all_tags.update(op.context.tags)

        left.markdown("**Select next step**")
        expander = left.expander("Filter operations with tags", expanded=False)
        with expander:
            selected_tags = st.multiselect(
                label="Tags", options=all_tags, key=f"{key}_tags"
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
            label="Operation", options=sorted(ops), key=f"{key}_op_select"
        )
        if selected:
            with right:
                with st.expander("Operation details", expanded=False):
                    st.kiara.operation_info(selected)

            return operations[selected]
        else:
            return None

    def render_last_step(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: WorkflowSession,
        operation: Operation,
        fixed_input: Mapping[str, Value],
    ) -> None:

        if not workflow_session.pipeline_steps:
            return

        if workflow_session.last_step_processed:
            raise NotImplementedError()

    def write_workflow_details(
        self, st: DeltaGenerator, workflow_session: WorkflowSession
    ):

        st.write(workflow_session.values)
        st.write(workflow_session.pipeline_steps)

    def add_step(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: WorkflowSession,
        operation: OperationInfo,
        value: Value,
    ) -> None:

        print("ADD STEP")

        idx = len(workflow_session.pipeline_steps)
        pipeline_step = workflow_session.workflow.add_step(
            operation=operation.operation.operation_id
        )

        workflow_session.pipeline_steps.append(pipeline_step.step_id)

        matches = {}
        for input_name, input_schema in operation.operation.inputs_schema.items():
            if input_schema.type == value.data_type_name:
                matches[input_name] = input_schema

        if not matches:
            raise Exception("Invalid input value, this is probably a bug.")
        elif len(matches) > 1:
            selected = st.selectbox(
                label="Select input", options=list(matches.keys()), key=key
            )
            name = generate_pipeline_endpoint_name(pipeline_step.step_id, selected)
        else:
            name = generate_pipeline_endpoint_name(
                pipeline_step.step_id, next(iter(matches.keys()))
            )

        workflow_session.values.setdefault(idx, {})[name] = value
        workflow_session.workflow.set_input(name, value)
        workflow_session.last_step_processed = False
        print(f"Last op: {operation.operation.operation_id}")
        workflow_session.last_operation = operation

    def ask_for_inputs(
        self, st: DeltaGenerator, key: str, missing_inputs: Dict[str, ValueSchema]
    ) -> Dict[str, Value]:

        comp = self.kiara.get_component("input_fields")
        kwargs = {PROFILE_KEYWORD: "default"}
        new_inputs = comp.render_func(st, key)(missing_inputs, **kwargs)
        return new_inputs

    def write_step_details(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: WorkflowSession,
        step_id: str,
        idx: int,
    ) -> None:

        for field, value in workflow_session.values[idx].items():
            st.markdown(f"#### Input: **{field}**")
            comp = st.kiara.get_component("preview")
            comp.render_func(st, key=f"{key}_value_{field}")(value)

    def write_step_desc(
        self, st: DeltaGenerator, key: str, pipeline_step: PipelineStep
    ) -> None:

        left, right = st.columns((1, 10))
        left.write("Step description")
        doc = None
        if not pipeline_step.doc.is_set:
            op_id = self.api.find_operation_id(
                pipeline_step.module_type, pipeline_step.module_config
            )
            if op_id is not None:
                op = self.api.get_operation(op_id)
                doc = op.doc
        if not doc:
            doc = DocumentationMetadataModel()
        right.markdown(doc.full_doc)

    def write_step_input_fields(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: WorkflowSession,
        step_id: str,
        idx: int,
    ) -> Mapping[str, Value]:

        workflow = workflow_session.workflow

        fixed_input = workflow_session.values[idx]
        field_name = next(iter(fixed_input.keys()))
        value = fixed_input[field_name]

        # set_inputs = {}
        # missing_values = set()
        # for field_name, inp_val in workflow.current_input_values.items():
        #     if inp_val.is_set:
        #         set_inputs[field_name] = inp_val
        #     else:
        #         missing_values.add(field_name)

        missing_fields = {}
        for _f, schema in workflow.current_inputs_schema.items():
            if _f == field_name:
                continue
            missing_fields[_f] = schema

        step = workflow.get_step(step_id)
        _key = f"{key}_missing_inputs_step_{step.step_id}"

        with st.expander(
            label=f"Auto-applied input using data from above", expanded=False
        ):
            f = field_name.split("__")[-1]
            st.markdown(f"Input '**{f}**', data type: `{value.data_type_name}`")
            comp = self._kiara_streamlit.get_component("preview")
            comp.render_func(st, key=f"{key}_preview_value_{field_name}")(value)

        with st.expander(label=f"Provide missing operation inputs", expanded=True):
            if not missing_fields:
                st.write("No additional inputs necessary.")
                new_inputs = {}
            else:
                new_inputs = self.ask_for_inputs(st, _key, missing_fields)

        assert field_name not in new_inputs
        result = {field_name: value}
        for k, v in new_inputs.items():
            result[k] = v

        return result

    def display_current_outputs(
        self, st: DeltaGenerator, key: str, workflow_session: WorkflowSession
    ) -> Union[None, Value]:

        st.write("OUTPUTS")
        fields = workflow_session.workflow.current_output_values
        comp = self._kiara_streamlit.get_component("values_preview")
        selected_value = comp.render_func(st, key=key)(values=fields)
        return selected_value

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        workflow_session: WorkflowSession = kwargs.pop("workflow_session", None)
        init_value: Union[None, Value] = kwargs.pop("init_value", None)
        if not workflow_session and args:
            workflow_session = args[0]
        if not init_value and len(args) >= 2:
            init_value = args[1]

        if not init_value:
            st.write("No initial value.")
            return

        # with st.expander(label="Workflow details", expanded=False):
        #     workflow_details = st.empty()

        st.markdown("---")

        RIGHT = 4
        left, right = st.columns((1, RIGHT))

        right.write()
        right.write()

        if len(workflow_session.pipeline_steps) > 1:
            for idx, step_id in enumerate(workflow_session.pipeline_steps[0:-1]):
                with st.expander(label=f"Step {idx+1}: {step_id}", expanded=True):
                    self.write_step_details(
                        st,
                        key=f"step_details_{key}_{step_id}",
                        workflow_session=workflow_session,
                        step_id=step_id,
                        idx=idx,
                    )

        next_operation = self.ask_for_next_step(
            st=st,
            key=f"{key}_ask_next_value_{len(workflow_session.pipeline_steps)}",
            value=init_value,
            left=left,
            right=right,
        )

        last_value = init_value

        if workflow_session.last_operation:
            print(f"LAST OP: {workflow_session.last_operation.operation.operation_id}")
        else:
            print("LAST OP: None")
        if next_operation:
            print(f"NEXT OP: {next_operation.operation.operation_id}")
        else:
            print("NEXT OP: None")

        if workflow_session.last_operation:
            if next_operation:
                operation_changed = (
                    workflow_session.last_operation.operation.operation_id
                    != next_operation.operation.operation_id
                )
            else:
                operation_changed = True
        else:
            operation_changed = True

        print(f"OP CHANGED: {operation_changed}")
        if operation_changed:
            if next_operation:
                self.remove_last_step(workflow_session=workflow_session)
                self.add_step(
                    st=st,
                    workflow_session=workflow_session,
                    operation=next_operation,
                    value=last_value,
                    key=f"{key}_add_step",
                )
                st.experimental_rerun()
            else:
                self.remove_last_step(workflow_session=workflow_session)
                workflow_session.last_operation = next_operation

        if not workflow_session.last_operation:
            return

        left.write(workflow_session.last_operation.documentation.description)

        with right:

            pipeline_step = workflow_session.pipeline_steps[-1]
            idx = len(workflow_session.pipeline_steps) - 1

            print(pipeline_step)

            current_inputs = self.write_step_input_fields(
                st=st,
                key=key,
                workflow_session=workflow_session,
                step_id=pipeline_step,
                idx=idx,
            )

        try:
            workflow_session.workflow.set_inputs(**current_inputs)
        except Exception as e:
            st.write(e)

        left, right = st.columns((1, RIGHT))
        process = right.button("Process")
        if process:
            with st.spinner("Processing..."):
                try:
                    workflow_session.last_step_processed = True
                    job_ids, errors = workflow_session.workflow.process_steps()
                except Exception as e:
                    right.error(e)

                for step_id, error in errors.items():
                    right.error(error.error)

            selected_value = self.display_current_outputs(
                right,
                key=f"{key}_display_current_outputs",
                workflow_session=workflow_session,
            )
        elif workflow_session.last_step_processed:
            selected_value = self.display_current_outputs(
                right,
                key=f"{key}_display_current_outputs",
                workflow_session=workflow_session,
            )
        else:
            selected_value = None

        if selected_value:
            workflow_session.last_step_processed = False
            st.write("NEXT STEP")
        # self.write_workflow_details(workflow_details, workflow_session)

        # st.write(new_inputs)

        # st.markdown(f"### Step: {step.step_id}")
        #
        # with st.expander(label="Previously set inputs", expanded=False):
        #     preview = self.kiara.get_component("values_preview")
        #     _key = f"{key}_preview_set_inputs"
        #     preview.render_func(st, _key)(set_inputs)
        #
        # _key = f"{key}_missing_inputs_step_{step.step_id}"
        # with st.expander(label="Please provide step inputs", expanded=True):
        #     new_inputs = self.ask_for_inputs(st, _key, missing_inputs)
        #
        # try:
        #     workflow.set_inputs(**new_inputs)
        # except Exception as e:
        #     st.error(f"Error: {e}")
        #     return
        #
        # process = st.button(label="Process step")
        # if process:
        #     with st.spinner('Processing...'):
        #         try:
        #             workflow.process_steps()
        #         except Exception as e:
        #             st.error(f"Processing error: {e}")
        #             return
        #
        # with st.expander(label="Current outputs", expanded=True):
        #     preview = self.kiara.get_component("values_preview")
        #     _key = f"{key}_preview_current_outputs"
        #     preview.render_func(st, _key)(workflow.current_output_values)
