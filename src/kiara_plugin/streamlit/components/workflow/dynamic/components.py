# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Dict, Mapping, Tuple, TypeVar, Union

from pydantic import ConfigDict, Field

from kiara.api import Value
from kiara.models.module.operation import Operation
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.preview import PreviewOptions
from kiara_plugin.streamlit.components.workflow.dynamic import WorkflowSessionDynamic
from streamlit.delta_generator import DeltaGenerator

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class DynamicWorkflowOptions(ComponentOptions):

    session: WorkflowSessionDynamic = Field(description="The current workflow session.")


DYN_WORKFLOW_OPTIONS_TYPE = TypeVar(
    "DYN_WORKFLOW_OPTIONS_TYPE", bound=DynamicWorkflowOptions
)


class DynamicWorkflowComponent(KiaraComponent[DYN_WORKFLOW_OPTIONS_TYPE]):

    # _component_name = "dynamic_workflow"
    _options = DynamicWorkflowOptions  # type: ignore


class StepDetailsOptions(DynamicWorkflowOptions):

    step_id: str = Field(description="The id of the step to show details for.")


class WriteStepComponent(DynamicWorkflowComponent):

    _component_name = "write_step_details"
    _options = StepDetailsOptions  # type: ignore

    def _render(self, st: "KiaraStreamlitAPI", options: StepDetailsOptions):

        idx = options.session.pipeline_steps.index(options.step_id)

        with st.expander("Operation", expanded=False):
            operation_id = options.session.operations[idx].operation.operation_id
            comp = self._kiara_streamlit.get_component("operation_info")
            comp.render_func(st)(
                operation_id, key=options.create_key(options.step_id, "operation_info")
            )

        with st.expander("Inputs", expanded=False):
            field_names = list(options.session.input_values[idx].keys())
            tabs = st.tabs([x.split("__")[-1] for x in field_names])
            for idx, field in enumerate(field_names):
                # _key = options.create_key("input", "preview", field)
                # self.kiara_streamlit.preview(key=_key, value=value)
                comp = self.get_component("preview")
                _key = options.create_key(options.step_id, "input", "value", field)
                value = options.session.input_values[idx][field]
                comp.render_func(tabs[idx])(key=_key, value=value)

        with st.expander("Outputs", expanded=False):
            field_names = list(options.session.output_values[idx].keys())
            tabs = st.tabs([x.split("__")[-1] for x in field_names])
            for idx, field in enumerate(field_names):
                comp = self.get_component("preview")
                _key = options.create_key(options.step_id, "output", "value", field)
                value = options.session.output_values[idx][field]
                comp.render_func(tabs[idx])(key=_key, value=value)


class NextStepOptions(DynamicWorkflowOptions):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: Value = Field(description="The value to use for the next step.")
    columns: Union[Tuple[int, int], Tuple[DeltaGenerator, DeltaGenerator]] = Field(
        description="The column layout to use for the next step.", default=(1, 4)
    )


class NextStepComponent(DynamicWorkflowComponent):

    _component_name = "ask_next_step"
    _options = NextStepOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: NextStepOptions
    ) -> Tuple[Union[Operation, None], Union[str, None]]:

        value = options.value

        if isinstance(options.columns[0], int):
            left, right = st.columns(options.columns)
        else:
            left, right = options.columns

        operations = self.api.retrieve_operations_info(input_types=value.data_type_name)
        all_tags = set()
        for op in operations.item_infos.values():
            all_tags.update(op.context.tags)

        left.markdown("**Select next step**")

        selectbox_placeholder = left.empty()

        expander = left.expander("Filter available operations", expanded=False)
        with expander:
            op_filter = st.text_input(
                label="filter tokens",
                value="",
                key=options.create_key("filter", "value"),
            )
            selected_tags = st.multiselect(
                label="Tags", options=all_tags, key=options.create_key("tags")
            )

        ops = dict(operations.item_infos)
        if op_filter:
            temp = {}
            for op_id, op in ops.items():
                if op_filter in op_id:
                    temp[op_id] = op
            ops = temp
        if selected_tags:
            temp = {}
            for op_id, op in ops.items():
                match = True
                for tag in selected_tags:
                    if tag not in op.context.tags:
                        match = False
                        break
                if match:
                    temp[op_id] = op
            ops = temp

        with selectbox_placeholder.container():
            selected = st.selectbox(
                label="Operation",
                options=sorted(ops.keys()),
                key=options.create_key("operation_select"),
            )
            show_op_details = st.checkbox("Show operation details", value=False)
            if selected:
                right.write("")
                right.write("")
                if show_op_details:
                    with right:
                        with st.expander("Operation details", expanded=True):
                            self.kiara_streamlit.operation_info(selected)
                st.write(operations[selected].documentation.description)

                field_name_placeholder = st.empty()
                field_name_desc_placeholder = st.empty()

                matches = {}
                for field_name, schema in operations[
                    selected
                ].operation.inputs_schema.items():
                    if schema.type == value.data_type_name:
                        matches[field_name] = schema

                if not matches:
                    raise Exception(
                        "No matching inputs found for value, this is most likely a bug."
                    )
                elif len(matches) == 1:
                    field_name = next(iter(matches.keys()))
                else:
                    field_name = field_name_placeholder.selectbox(
                        label="Select input field to use for value",
                        options=sorted(matches.keys()),
                    )
                    field_name_desc_placeholder.markdown(
                        matches[field_name].doc.description
                    )

                return operations[selected], field_name
            else:
                return None, None


class StepInputFields(DynamicWorkflowComponent):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    _component_name = "step_input_fields"
    _options = StepDetailsOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: StepDetailsOptions
    ) -> Dict[str, Value]:

        step_id = options.step_id
        idx = options.session.pipeline_steps.index(step_id)
        workflow = options.session.workflow

        fixed_input = options.session.input_values[idx]
        assert len(fixed_input) == 1
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
                comp = self.kiara_streamlit.get_component("inputs_for_fields")
                _key = options.create_key("missing_inputs_fields", step.step_id)
                new_inputs = comp.render_func(st)(key=_key, fields=missing_fields)

        assert field_name not in new_inputs
        result = {field_name: value}
        for k, v in new_inputs.items():
            result[k] = v

        return result


class CurrentValuesPreviewOptions(ComponentOptions):
    values: Mapping[str, Value] = Field(description="The values to display.")
    add_value_types: bool = Field(
        description="Whether to add the type of the value to the tab titles.",
        default=True,
    )


class CurrentValuesPreview(KiaraComponent[CurrentValuesPreviewOptions]):

    _component_name = "current_values_preview"
    _options = CurrentValuesPreviewOptions

    def _render(
        self,
        st: "KiaraStreamlitAPI",
        options: CurrentValuesPreviewOptions,
    ) -> Union[Value, None]:

        if not options.values:
            st.write("-- no values --")
            return None

        field_names = sorted(options.values.keys())
        if not options.add_value_types:
            tab_names = field_names
        else:
            tab_names = sorted(
                (
                    f"{x} ({options.values[x].data_type_name})"
                    for x in options.values.keys()
                )
            )

        tabs = st.tabs(tab_names)
        selected = None
        for idx, field in enumerate(field_names):

            value = options.values[field]
            component = self.kiara_streamlit.get_preview_component(value.data_type_name)
            if component is None:
                component = self.kiara_streamlit.get_preview_component("any")
            left, center, right = tabs[idx].columns([1, 4, 1])

            _key = options.create_key("select", f"{idx}_{field}")
            select = left.button("Select for next step", key=_key)
            _key = options.create_key("preview", f"{idx}_{field}")
            preview_opts = PreviewOptions(key=_key, value=value)
            component.render_preview(st=center, options=preview_opts)  # type: ignore

            right.write("Save value")
            with right.form(key=options.create_key("save_form", f"{idx}_{field}")):
                _key = options.create_key("alias", f"{idx}_{field}")
                alias = self._st.text_input(
                    "alias",
                    value="",
                    key=_key,
                    placeholder="alias",
                    label_visibility="hidden",
                )
                _key = options.create_key("save", f"{idx}_{field}")
                save = self._st.form_submit_button("Save")

            if save and alias:
                store_result = self.api.store_value(
                    value=value, alias=alias, allow_overwrite=False
                )
                if store_result.error:
                    right.error(store_result.error)
                else:
                    right.success("Value saved")
            if select:
                selected = field

        if selected:
            return options.values[selected]
        else:
            return None
