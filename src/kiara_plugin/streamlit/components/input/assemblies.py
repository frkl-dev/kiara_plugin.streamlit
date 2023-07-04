# -*- coding: utf-8 -*-
import abc
import uuid
from typing import TYPE_CHECKING, Any, Dict, Mapping, TypeVar, Union

from pydantic import Field

from kiara.api import ValueMap, ValueSchema
from kiara.registries.data import ValueLink
from kiara.utils.values import construct_valuemap
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.input import DefaultInputOptions, InputComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class AssemblyOptions(ComponentOptions):

    max_columns: int = Field(
        description="The maximum number of columns to use for the assembly.", default=3
    )
    profile: str = Field(
        description="The name of the profile that renders the assembly. Available: 'default' and 'all'",
        default="default",
    )
    smart_label: bool = Field(
        description="Whether to try to shorten the label.", default=True
    )


ASSEMBLY_OPTIONS_TYPE = TypeVar("ASSEMBLY_OPTIONS_TYPE", bound=AssemblyOptions)


class InputAssemblyComponent(KiaraComponent[ASSEMBLY_OPTIONS_TYPE]):

    _options = AssemblyOptions  # type: ignore

    @abc.abstractmethod
    def get_input_fields(
        self, options: ASSEMBLY_OPTIONS_TYPE
    ) -> Mapping[str, ValueSchema]:
        pass

    def _render(
        self, st: "KiaraStreamlitAPI", options: ASSEMBLY_OPTIONS_TYPE
    ) -> ValueMap:

        profile = options.profile

        method_name = f"render_{profile}"
        if not hasattr(self, method_name):
            raise Exception(f"No input fields render profile '{profile}' available.'")

        fields = self.get_input_fields(options=options)
        func = getattr(self, method_name)
        result = func(st, fields, options=options)

        value_map = self.api.assemble_value_map(result, values_schema=fields)
        return value_map

    def render_all(
        self,
        st: "KiaraStreamlitAPI",
        fields: Mapping[str, ValueSchema],
        options: ASSEMBLY_OPTIONS_TYPE,
    ) -> Mapping[str, Union[str, uuid.UUID, ValueLink, None]]:

        max_columns = options.max_columns

        if not fields:
            return construct_valuemap(kiara_api=self.api, values={})

        if not max_columns:
            num_columns = len(fields)
        elif len(fields) >= max_columns:
            num_columns = max_columns
        else:
            num_columns = len(fields)

        columns = st.columns(num_columns)
        values: Dict[str, Union[None, ValueLink, str, uuid.UUID]] = {}
        for idx, field_name in enumerate(fields.keys()):
            schema = fields[field_name]
            help = None
            if schema.doc.is_set:
                help = schema.doc.full_doc
            data_type_name = schema.type
            _key = options.create_key("op_input", "req", "all", field_name)
            comp: InputComponent = self.kiara_streamlit.get_input_component(
                data_type_name
            )

            column_idx = idx % num_columns
            input_opts = DefaultInputOptions(
                key=_key,
                label=field_name,
                value_schema=schema,
                help=help,
                smart_label=options.smart_label,
            )
            r = comp.render_input_field(columns[column_idx], input_opts)  # type: ignore

            values[field_name] = r

        return values

    def render_default(
        self,
        st: "KiaraStreamlitAPI",
        fields: Mapping[str, ValueSchema],
        options: AssemblyOptions,
    ) -> Mapping[str, Union[str, None, uuid.UUID, ValueLink]]:

        required: Dict[str, ValueSchema] = {}
        optional: Dict[str, ValueSchema] = {}
        max_columns = options.max_columns

        optional_expanded = True

        for input_name, input_schema in fields.items():
            if not input_schema.optional:
                required[input_name] = input_schema
            else:
                optional[input_name] = input_schema

        values = {}
        if required:
            req_expander = st.expander("Required inputs", expanded=True)
            if not max_columns:
                num_columns = len(required)
            elif len(required) >= max_columns:
                num_columns = max_columns
            else:
                num_columns = len(required)

            columns = req_expander.columns(num_columns)
            for idx, field_name in enumerate(required.keys()):
                schema = required[field_name]
                help = None
                if schema.doc.is_set:
                    help = schema.doc.full_doc
                data_type_name = schema.type
                _key = options.create_key("op_input", "req", "default", field_name)
                comp = self.kiara_streamlit.get_input_component(data_type_name)

                column_idx = idx % num_columns
                input_opts = DefaultInputOptions(
                    key=_key,
                    label=field_name,
                    value_schema=schema,
                    help=help,
                    smart_label=options.smart_label,
                )

                r = comp.render_input_field(columns[column_idx], input_opts)  # type: ignore

                values[field_name] = r

        if optional:
            opt_expander = st.expander("Optional inputs", expanded=optional_expanded)

            if not max_columns:
                num_columns = len(optional)
            elif len(optional) >= max_columns:
                num_columns = max_columns
            else:
                num_columns = len(optional)

            opt_columns = opt_expander.columns(num_columns)

            for idx, field_name in enumerate(optional.keys()):
                schema = optional[field_name]
                help = None
                if schema.doc.is_set:
                    help = schema.doc.full_doc

                if idx >= num_columns:
                    if idx % num_columns == 0:
                        opt_columns = opt_expander.columns(num_columns)

                data_type_name = schema.type
                _key = options.create_key("op_input", "opt", "default", field_name)
                comp = self.kiara_streamlit.get_input_component(data_type_name)
                column_idx = idx % num_columns
                input_opts = DefaultInputOptions(
                    key=_key,
                    label=field_name,
                    value_schema=schema,
                    help=help,
                    smart_label=options.smart_label,
                )

                r = comp.render_input_field(opt_columns[column_idx], input_opts)  # type: ignore
                values[field_name] = r

        return values


class OperationInputsOptions(AssemblyOptions):
    operation_id: str = Field(
        description="The id of the operation to render the inputs for."
    )
    module_config: Union[Dict[str, Any], None] = Field(
        description="Optional module config.", default=None
    )


class OperationInputs(InputAssemblyComponent):
    """Render all inputs for a specifc operation."""

    _component_name = "operation_inputs"
    _options = OperationInputsOptions  # type: ignore
    _examples = [
        {
            "doc": "Render the inputs for the 'table_filter.select_rows' operation.",
            "args": {"operation_id": "table_filter.select_rows"},
        }
    ]

    def get_input_fields(
        self, options: OperationInputsOptions
    ) -> Mapping[str, ValueSchema]:

        # TODO: check argument
        data = {
            "module_type": options.operation_id,
            "module_config": options.module_config,
        }
        op = self.api.get_operation(data)
        return op.inputs_schema


class InputFieldsOptions(AssemblyOptions):
    fields: Mapping[str, ValueSchema] = Field(description="The fields to render.")


class InputFields(InputAssemblyComponent):
    """Render a panel containing input widgets for each of the provided fields.

    The type of input widgets is determined by the type of each field schema.
    """

    _component_name = "inputs_for_fields"
    _options = InputFieldsOptions  # type: ignore
    _examples = [
        {
            "doc": "Render inputs for 2 scalar field items.\n\nIn most cases, you would not build the field schemas up yourself, but use already existing 'inputs_schema' object attached to operations or workflows.",
            "args": {
                "fields": {
                    "text_field": {
                        "type": "string",
                        "doc": "A text field.",
                    },
                    "number_field": {"type": "integer", "doc": "A number."},
                }
            },
        }
    ]

    def get_input_fields(
        self, options: InputFieldsOptions
    ) -> Mapping[str, ValueSchema]:
        return options.fields
