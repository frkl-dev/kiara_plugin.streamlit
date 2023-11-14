# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, List, Union

from kiara.api import Value
from kiara.interfaces.python_api import OperationInfo
from kiara.models.documentation import DocumentationMetadataModel
from kiara.models.module.pipeline import PipelineStep, generate_pipeline_endpoint_name
from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.components.workflow.dynamic import (
    LEFT_COLUMN,
    RIGHT_COLUMN,
    WorkflowSessionDynamic,
)
from kiara_plugin.streamlit.components.workflow.dynamic.components import (
    DynamicWorkflowOptions,
)
from streamlit.delta_generator import DeltaGenerator

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class DynamicWorkflow(KiaraComponent):

    _component_name = "workflow_dynamic"
    _options = DynamicWorkflowOptions

    def remove_last_step(self, workflow_session: WorkflowSessionDynamic) -> None:

        if workflow_session.pipeline_steps:
            idx = len(workflow_session.pipeline_steps) - 1
            last_step = workflow_session.pipeline_steps.pop()
            try:
                workflow_session.input_values.pop(idx)
            except Exception:
                pass
            try:
                workflow_session.operations.pop(idx)
            except Exception:
                pass

            try:
                workflow_session.output_values.pop(idx)
            except Exception:
                pass
            workflow_session.workflow.clear_steps(last_step)

        workflow_session.last_step_processed = False

    def write_workflow_details(
        self, st: "KiaraStreamlitAPI", workflow_session: WorkflowSessionDynamic
    ):

        st.write(workflow_session.input_values)
        st.write(workflow_session.pipeline_steps)

    def add_step(
        self,
        workflow_session: WorkflowSessionDynamic,
        operation: OperationInfo,
    ) -> None:

        pipeline_step = workflow_session.workflow.add_step(
            operation=operation.operation.operation_id
        )

        workflow_session.pipeline_steps.append(pipeline_step.step_id)

        workflow_session.last_step_processed = False
        workflow_session.current_outputs = None
        workflow_session.last_operation = operation

    def write_step_desc(
        self, st: "KiaraStreamlitAPI", key: str, pipeline_step: PipelineStep
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

    def display_current_outputs(
        self,
        st: "KiaraStreamlitAPI",
        key: str,
        workflow_session: WorkflowSessionDynamic,
        step_id: str,
    ) -> Union[None, Value]:

        if workflow_session.current_outputs is None:

            step_fields = workflow_session.workflow.get_current_outputs_schema_for_step(
                step_id
            )
            outputs = {}
            for field_name in step_fields.keys():
                value = workflow_session.workflow.current_output_values.get_value_obj(
                    field_name
                )
                smart_field_name = field_name.split("__")[-1]
                outputs[smart_field_name] = value

            workflow_session.current_outputs = outputs

        comp = self._kiara_streamlit.get_component("current_values_preview")
        selected_value: Union[None, Value] = comp.render_func(st)(
            key=f"{key}_preview_result_{step_id}",
            values=workflow_session.current_outputs,
        )
        return selected_value

    def write_columns(self, st: "KiaraStreamlitAPI") -> List[DeltaGenerator]:

        columns: List[DeltaGenerator] = st.columns((LEFT_COLUMN, RIGHT_COLUMN))
        return columns

    def write_separator(self, st: "KiaraStreamlitAPI") -> None:

        st.markdown("---")

    def _render(self, st: "KiaraStreamlitAPI", options: DynamicWorkflowOptions):

        session: WorkflowSessionDynamic = options.session
        if session.workflow is None:
            session.workflow = self.api.create_workflow()

        current_value: Union[None, Value] = session.current_value

        left, right = self.write_columns(st)

        if not current_value or (
            len(session.pipeline_steps) == 1 and not session.last_step_processed
        ):
            # if we are at the beginning, without anything processed yet, we want to give
            # Users the option to change the initial value

            with left:
                init_value: Value = self.kiara_streamlit.select_value(
                    label="**Select initial value**", preview=False
                )

            right.write("")
            right.write("")
            with right.expander("Value preview", expanded=False):
                if init_value:
                    self.kiara_streamlit.preview(init_value)
                else:
                    st.write("-- no value --")

            if not init_value:
                st.write("No value selected, doing nothing...")
                return
            else:
                session.current_value = init_value
                if session.initial_value is None or len(session.pipeline_steps) < 2:
                    # we have to record the initial value, once
                    session.initial_value = init_value
                current_value = init_value
        else:
            assert session.initial_value is not None
            left.markdown(f"**Initial value** ({session.initial_value.data_type_name})")
            with right.expander("Value preview", expanded=False):
                if current_value:
                    assert session.initial_value is not None
                    self.kiara_streamlit.preview(session.initial_value)
            reset = left.button("Reset")
            if reset:
                workflow = self.api.create_workflow()
                options.session.reset(workflow)
                st.experimental_rerun()

        self.write_separator(st)

        # if there are previously computed steps, we want to print details about them here, so users can
        # refer back to them

        if session.pipeline_steps:
            # skip if we have selected an operation, but haven't processed anything yet
            if session.last_step_processed or len(session.pipeline_steps) > 1:
                left, right = self.write_columns(st)

                # align vertically as good as possible
                right.write()
                right.write()

                left.write("**Previous steps**")
                for idx, step_id in enumerate(session.pipeline_steps[0:-1]):
                    step_details = right.expander(
                        label=f"Step {idx+1}: {step_id}", expanded=False
                    )
                    _key = options.create_key("previous_step_details", step_id)
                    with step_details:
                        self.kiara_streamlit.write_step_details(
                            key=_key, step_id=step_id, session=session
                        )

                self.write_separator(st)
                left, right = self.write_columns(st)

                right.write()
                right.write()
                left.markdown(f"**Current value** ({current_value.data_type_name})")
                with right.expander("Preview", expanded=False):
                    self._kiara_streamlit.preview(
                        current_value, key=options.create_key("preview_current_value")
                    )

        # now we want to ask for the next operation to apply to the current value
        left, right = self.write_columns(st)

        next_operation, field_name = self.kiara_streamlit.ask_next_step(
            columns=(left, right),
            value=current_value,
            session=session,
            key=options.create_key("ask_next_step"),
        )

        # now we need to check if the operation itself changed during the last cycle
        if session.last_operation:
            if next_operation:
                operation_changed = (
                    session.last_operation.operation.operation_id
                    != next_operation.operation.operation_id
                )
            else:
                operation_changed = True
        else:
            operation_changed = True

        if operation_changed:
            if next_operation:
                if not session.last_step_processed:
                    self.remove_last_step(workflow_session=session)
                self.add_step(
                    workflow_session=session,
                    operation=next_operation,
                )
                st.experimental_rerun()
            else:
                self.remove_last_step(workflow_session=session)
                session.last_operation = next_operation

        if not session.last_operation:
            # if there is no loperation, there is nothing to do
            return

        if session.pipeline_steps:
            pipeline_step = session.pipeline_steps[-1]
        else:
            pipeline_step = None

        assert pipeline_step
        assert current_value
        assert field_name

        name = generate_pipeline_endpoint_name(pipeline_step, field_name)
        session.input_values[session.pipeline_steps.index(pipeline_step)] = {
            name: current_value
        }
        session.operations[
            session.pipeline_steps.index(pipeline_step)
        ] = session.last_operation
        session.workflow.clear_current_inputs_for_step(pipeline_step)

        session.workflow.set_input(field_name=name, value=current_value)

        with right:
            _key = options.create_key("step_input_fields", pipeline_step)
            current_inputs = self.kiara_streamlit.step_input_fields(
                key=_key, session=session, step_id=pipeline_step
            )

        try:
            session.workflow.set_inputs(**current_inputs)
        except Exception as e:
            st.write(e)

        # left, right = self.write_columns(st)

        process = right.button("Process")
        if process:
            with st.spinner("Processing..."):  # type: ignore
                errors = {}
                try:
                    session.last_step_processed = True
                    session.current_outputs = None
                    job_ids, errors = session.workflow.process_steps()
                except Exception as e:
                    right.error(e)

                for _step_id, error in errors.items():
                    right.error(error.error)
            _key = options.create_key("display_current_outputs")

            step_fields = session.workflow.get_current_outputs_schema_for_step(
                pipeline_step
            )
            temp = {}
            for field_name in step_fields.keys():
                value = session.workflow.current_output_values.get_value_obj(field_name)
                temp[field_name] = value
            session.output_values[session.pipeline_steps.index(pipeline_step)] = temp

            selected_value = self.display_current_outputs(
                right, key=_key, workflow_session=session, step_id=pipeline_step
            )
        elif session.last_step_processed:
            _key = options.create_key("display_current_outputs")
            selected_value = self.display_current_outputs(
                right, key=_key, workflow_session=session, step_id=pipeline_step  # type: ignore
            )
        else:
            selected_value = None

        if selected_value:
            session.current_value = selected_value
            session.last_operation = None
            st.experimental_rerun()
