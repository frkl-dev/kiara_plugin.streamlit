# -*- coding: utf-8 -*-
from typing import List, Union

from kiara import Value
from kiara.interfaces.python_api import OperationInfo
from kiara.models.documentation import DocumentationMetadataModel
from kiara.models.module.pipeline import PipelineStep, generate_pipeline_endpoint_name
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.components.workflow.dynamic import (
    LEFT_COLUMN,
    RIGHT_COLUMN,
    DynamicWorkflowSession,
)
from kiara_plugin.streamlit.components.workflow.dynamic.components import (
    DynamicWorkflowOptions,
)


class DynamicWorkflow(KiaraComponent):

    _component_name = "workflow"
    _options = DynamicWorkflowOptions

    def remove_last_step(self, workflow_session: DynamicWorkflowSession) -> None:

        if workflow_session.pipeline_steps:
            idx = len(workflow_session.pipeline_steps) - 1
            last_step = workflow_session.pipeline_steps.pop()
            try:
                workflow_session.values.pop(idx)
            except Exception:
                pass
            workflow_session.workflow.clear_steps(last_step)

        workflow_session.last_step_processed = False

    # def ask_for_next_step(
    #     self,
    #     st: DeltaGenerator,
    #     left: DeltaGenerator,
    #     right: DeltaGenerator,
    #     key: str,
    #     value: Value,
    # ) -> Union[None, OperationInfo]:
    #
    #     operations = self.api.get_operations_info(input_types=value.data_type_name)
    #     all_tags = set()
    #     for op in operations.item_infos.values():
    #         all_tags.update(op.context.tags)
    #
    #     left.markdown("**Select next step**")
    #     expander = left.expander("Filter operations", expanded=False)
    #     with expander:
    #         selected_tags = st.multiselect(
    #             label="Tags", options=all_tags, key=f"{key}_tags"
    #         )
    #
    #     if selected_tags:
    #         ops = []
    #
    #         for op_id, op in operations.item_infos.items():
    #             match = True
    #             for tag in selected_tags:
    #                 if tag not in op.context.tags:
    #                     match = False
    #                     break
    #             if match:
    #                 ops.append(op_id)
    #     else:
    #         ops = operations.item_infos.keys()
    #
    #     selected = left.selectbox(
    #         label="Operation", options=sorted(ops), key=f"{key}_op_select"
    #     )
    #     if selected:
    #         right.write("")
    #         right.write("")
    #         with right:
    #             with st.expander("Operation details", expanded=False):
    #                 st.kiara.operation_info(selected)
    #
    #         return operations[selected]
    #     else:
    #         return None

    def write_workflow_details(
        self, st: DeltaGenerator, workflow_session: DynamicWorkflowSession
    ):

        st.write(workflow_session.values)
        st.write(workflow_session.pipeline_steps)

    def add_step(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: DynamicWorkflowSession,
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
            assert selected is not None
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

    # def ask_for_inputs(
    #     self, st: DeltaGenerator, key: str, missing_inputs: Dict[str, ValueSchema]
    # ) -> Dict[str, Value]:
    #
    #     comp = self.kiara_streamlit.get_component("input_fields")
    #     kwargs = {PROFILE_KEYWORD: "default"}
    #     new_inputs = comp.render_func(st, key)(missing_inputs, **kwargs)
    #     return new_inputs

    # def write_step_details(
    #     self,
    #     st: DeltaGenerator,
    #     key: str,
    #     workflow_session: DynamicWorkflowSession,
    #     step_id: str,
    #     idx: int,
    # ) -> None:
    #
    #     st.markdown("### Inputs")
    #     for field, value in workflow_session.values[idx].items():
    #         st.markdown(f"#### Input: **{field}**")
    #         comp = self.kiara_streamlit.get_component("preview")
    #         comp.render_func(st, key=f"{key}_value_{field}")(value)

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

    # def write_step_input_fields(
    #     self,
    #     st: DeltaGenerator,
    #     key: str,
    #     workflow_session: DynamicWorkflowSession,
    #     step_id: str,
    #     idx: int,
    # ) -> Mapping[str, Value]:
    #
    #     workflow = workflow_session.workflow
    #
    #     fixed_input = workflow_session.values[idx]
    #     field_name = next(iter(fixed_input.keys()))
    #     value = fixed_input[field_name]
    #
    #     # set_inputs = {}
    #     # missing_values = set()
    #     # for field_name, inp_val in workflow.current_input_values.items():
    #     #     if inp_val.is_set:
    #     #         set_inputs[field_name] = inp_val
    #     #     else:
    #     #         missing_values.add(field_name)
    #
    #     missing_fields = {}
    #     for _f, schema in workflow.get_current_inputs_schema_for_step(step_id).items():
    #         if _f == field_name:
    #             continue
    #         missing_fields[_f] = schema
    #
    #     step = workflow.get_step(step_id)
    #     _key = f"{key}_missing_inputs_step_{step.step_id}"
    #
    #     # with st.expander(
    #     #     label=f"Auto-applied input using data from above", expanded=False
    #     # ):
    #     #     f = field_name.split("__")[-1]
    #     #     st.markdown(f"Input '**{f}**', data type: `{value.data_type_name}`")
    #     #     comp = self._kiara_streamlit.get_component("preview")
    #     #     comp.render_func(st, key=f"{key}_preview_value_{field_name}")(value)
    #
    #     with st.expander(label=f"Provide missing operation inputs", expanded=True):
    #         if not missing_fields:
    #             st.write("No additional inputs necessary.")
    #             new_inputs = {}
    #         else:
    #             new_inputs = self.ask_for_inputs(st, _key, missing_fields)
    #
    #     assert field_name not in new_inputs
    #     result = {field_name: value}
    #     for k, v in new_inputs.items():
    #         result[k] = v
    #
    #     return result

    def display_current_outputs(
        self,
        st: DeltaGenerator,
        key: str,
        workflow_session: DynamicWorkflowSession,
        step_id: str,
    ) -> Union[None, Value]:

        step_fields = workflow_session.workflow.get_current_outputs_schema_for_step(
            step_id
        )
        outputs = {}
        for field_name in step_fields.keys():
            value = workflow_session.workflow.current_output_values.get_value_obj(
                field_name
            )
            outputs[field_name.split("__")[-1]] = value
        comp = self._kiara_streamlit.get_component("values_preview")
        selected_value = comp.render_func(st)(
            key=f"{key}_preview_result_{field_name}", values=outputs
        )
        return selected_value

    def write_columns(self, st: DeltaGenerator) -> List[DeltaGenerator]:

        columns = st.columns((LEFT_COLUMN, RIGHT_COLUMN))
        return columns

    def write_separator(self, st: DeltaGenerator) -> None:

        st.markdown("---")

    def _render(self, st: DeltaGenerator, options: DynamicWorkflowOptions):

        session: DynamicWorkflowSession = options.session
        current_value: Union[None, Value] = session.current_value

        left, right = self.write_columns(st)

        if not current_value or (
            len(session.pipeline_steps) == 1 and not session.last_step_processed
        ):
            # if we are at the beginning, without anything processed yet, we want to give
            # Users the option to change the initial value

            with left:
                init_value: Value = self.kiara_streamlit.value_input(
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
            left.write("**Initial value**")

            with right.expander("Value preview", expanded=False):
                if current_value:
                    assert session.initial_value is not None
                    self.kiara_streamlit.preview(session.initial_value)

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
                left.markdown("**Current value**")
                with right.expander("Preview", expanded=False):
                    self._kiara_streamlit.preview(
                        current_value, key=options.create_key("preview_current_value")
                    )

        # now we want to ask for the next operation to apply to the current value
        left, right = self.write_columns(st)

        next_operation = self.kiara_streamlit.ask_next_step(
            columns=(LEFT_COLUMN, RIGHT_COLUMN),
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

        print(f"OP CHANGED: {operation_changed}")
        if operation_changed:
            if next_operation:
                if not session.last_step_processed:
                    self.remove_last_step(workflow_session=session)
                self.add_step(
                    st=st,
                    workflow_session=session,
                    operation=next_operation,
                    value=current_value,
                    key=options.create_key("add_step"),
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

        left, right = self.write_columns(st)
        with right:
            _key = options.create_key("steP_input_fields", pipeline_step)
            current_inputs = self.kiara_streamlit.step_input_fields(
                key=_key, session=session, step_id=pipeline_step
            )

        try:
            session.workflow.set_inputs(**current_inputs)
        except Exception as e:
            st.write(e)

        left, right = self.write_columns(st)

        process = right.button("Process")
        if process:
            with st.spinner("Processing..."):  # type: ignore
                try:
                    session.last_step_processed = True
                    job_ids, errors = session.workflow.process_steps()
                except Exception as e:
                    right.error(e)

                for _step_id, error in errors.items():
                    right.error(error.error)
            _key = options.create_key("display_current_outputs")
            selected_value = self.display_current_outputs(
                right, key=_key, workflow_session=session, step_id=pipeline_step
            )
        elif session.last_step_processed:
            _key = options.create_key("display_current_outputs")
            selected_value = self.display_current_outputs(
                right, key=_key, workflow_session=session, step_id=pipeline_step
            )
        else:
            selected_value = None

        if selected_value:
            session.current_value = selected_value
            session.last_operation = None
            st.experimental_rerun()

    # def _render_old(self, st: DeltaGenerator, key: str, *args, **kwargs):
    #
    #     workflow_session: DynamicWorkflowSession = kwargs.pop("workflow_session", None)
    #     if not workflow_session and args:
    #         workflow_session = args[0]
    #
    #     current_value: Union[None, Value] = workflow_session.current_value
    #
    #     left, right = st.columns((1, 4))
    #
    #     if not current_value or (len(workflow_session.pipeline_steps) == 1 and not workflow_session.last_step_processed):
    #
    #         with left:
    #             init_value: Value = st.kiara.value_input(
    #                 label="**Select initial value**", preview=False
    #             )
    #
    #         right.write("")
    #         right.write("")
    #         with right.expander("Value preview", expanded=False):
    #             if init_value:
    #                 st.kiara.preview(init_value)
    #             else:
    #                 st.write("-- no value --")
    #
    #         if not init_value:
    #             st.write("No value selected, doing nothing...")
    #             return
    #         else:
    #             # self.remove_last_step(workflow_session)
    #             workflow_session.current_value = init_value
    #             if workflow_session.initial_value is None or len(workflow_session.pipeline_steps) < 2:
    #                 workflow_session.initial_value = init_value
    #             current_value = init_value
    #     else:
    #         left.write("**Initial value**")
    #
    #         with right.expander("Value preview", expanded=False):
    #             if current_value:
    #                 assert workflow_session.initial_value is not None
    #                 st.kiara.preview(workflow_session.initial_value)
    #
    #     st.markdown("---")
    #
    #     RIGHT = 4
    #
    #     if workflow_session.pipeline_steps:
    #         if workflow_session.last_step_processed or len(workflow_session.pipeline_steps) > 1:
    #             left, right = st.columns((1, RIGHT))
    #
    #             right.write()
    #             right.write()
    #
    #             left.write("**Previous steps**")
    #             for idx, step_id in enumerate(workflow_session.pipeline_steps[0:-1]):
    #                 step_details = right.expander(label=f"Step {idx+1}: {step_id}", expanded=False)
    #                 self.write_step_details(
    #                         st=step_details,
    #                         key=f"step_details_{key}_{step_id}",
    #                         workflow_session=workflow_session,
    #                         step_id=step_id,
    #                         idx=idx,
    #                     )
    #
    #
    #             st.markdown("---")
    #
    #             left, right = st.columns((1, RIGHT))
    #
    #             right.write()
    #             right.write()
    #             left.markdown("**Current value**")
    #             with right.expander("Preview", expanded=False):
    #                 self._kiara_streamlit.preview(workflow_session.current_value)
    #
    #     left, right = st.columns((1, RIGHT))
    #     next_operation = self.ask_for_next_step(
    #         st=st,
    #         key=f"{key}_ask_next_value_{len(workflow_session.pipeline_steps)}",
    #         value=current_value,
    #         left=left,
    #         right=right,
    #     )
    #
    #     if workflow_session.last_operation:
    #         print(f"LAST OP: {workflow_session.last_operation.operation.operation_id}")
    #     else:
    #         print("LAST OP: None")
    #     if next_operation:
    #         print(f"NEXT OP: {next_operation.operation.operation_id}")
    #     else:
    #         print("NEXT OP: None")
    #
    #     if workflow_session.last_operation:
    #         if next_operation:
    #             operation_changed = (
    #                 workflow_session.last_operation.operation.operation_id
    #                 != next_operation.operation.operation_id
    #             )
    #         else:
    #             operation_changed = True
    #     else:
    #         operation_changed = True
    #
    #     print(f"OP CHANGED: {operation_changed}")
    #     if operation_changed:
    #         if next_operation:
    #             if not workflow_session.last_step_processed:
    #                 self.remove_last_step(workflow_session=workflow_session)
    #             self.add_step(
    #                 st=st,
    #                 workflow_session=workflow_session,
    #                 operation=next_operation,
    #                 value=current_value,
    #                 key=f"{key}_add_step",
    #             )
    #             st.experimental_rerun()
    #         else:
    #             self.remove_last_step(workflow_session=workflow_session)
    #             workflow_session.last_operation = next_operation
    #
    #     if not workflow_session.last_operation:
    #         return
    #
    #     left.write(workflow_session.last_operation.documentation.description)
    #
    #     if workflow_session.pipeline_steps:
    #         pipeline_step = workflow_session.pipeline_steps[-1]
    #     else:
    #         pipeline_step = None
    #
    #
    #     with right:
    #
    #         idx = workflow_session.pipeline_steps.index(pipeline_step)
    #         current_inputs = self.write_step_input_fields(
    #             st=st,
    #             key=key,
    #             workflow_session=workflow_session,
    #             step_id=pipeline_step,
    #             idx=idx,
    #         )
    #
    #     try:
    #         workflow_session.workflow.set_inputs(**current_inputs)
    #     except Exception as e:
    #         st.write(e)
    #
    #     left, right = st.columns((1, RIGHT))
    #     process = right.button("Process")
    #     if process:
    #         with st.spinner("Processing..."):
    #             try:
    #                 workflow_session.last_step_processed = True
    #                 job_ids, errors = workflow_session.workflow.process_steps()
    #             except Exception as e:
    #                 right.error(e)
    #
    #             for _step_id, error in errors.items():
    #                 right.error(error.error)
    #         step_id = workflow_session.pipeline_steps[-1]
    #         selected_value = self.display_current_outputs(
    #             right,
    #             key=f"{key}_display_current_outputs",
    #             workflow_session=workflow_session,
    #             step_id=step_id
    #         )
    #     elif workflow_session.last_step_processed:
    #         step_id = workflow_session.pipeline_steps[-1]
    #         selected_value = self.display_current_outputs(
    #             right,
    #             key=f"{key}_display_current_outputs",
    #             workflow_session=workflow_session,
    #             step_id=step_id
    #         )
    #     else:
    #         selected_value = None
    #
    #     if selected_value:
    #         workflow_session.current_value = selected_value
    #         workflow_session.last_operation = None
    #         st.experimental_rerun()
