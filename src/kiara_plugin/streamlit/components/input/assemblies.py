# -*- coding: utf-8 -*-
import abc
import uuid
from typing import Dict, Mapping, TypeVar, Union

from kiara import ValueMap, ValueSchema
from kiara.registries.data import ValueLink
from kiara.utils.values import construct_valuemap
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.input import InputComponent, InputOptions


class AssemblyOptions(ComponentOptions):

    profile: str = Field(
        description="The name of the profile that renders the assembly.",
        default="default",
    )
    max_columns: int = Field(
        description="The maximum number of columns to use for the assembly.", default=3
    )


ASSEMBLY_OPTIONS_TYPE = TypeVar("ASSEMBLY_OPTIONS_TYPE", bound=AssemblyOptions)


class InputAssemblyComponent(KiaraComponent[ASSEMBLY_OPTIONS_TYPE]):

    _options = AssemblyOptions  # type: ignore

    @abc.abstractmethod
    def get_input_fields(
        self, options: ASSEMBLY_OPTIONS_TYPE
    ) -> Mapping[str, ValueSchema]:
        pass

    def _render(self, st: DeltaGenerator, options: ASSEMBLY_OPTIONS_TYPE):

        profile = options.profile

        method_name = f"render_{profile}"
        if not hasattr(self, method_name):
            raise Exception(f"No input fields render profile '{profile}' available.'")

        fields = self.get_input_fields(options=options)
        func = getattr(self, method_name)
        return func(st, fields, options=options)

    def render_all(
        self,
        st: DeltaGenerator,
        key: str,
        fields: Mapping[str, ValueSchema],
        options: ASSEMBLY_OPTIONS_TYPE,
    ) -> ValueMap:

        max_columns = options.max_columns

        if not fields:
            return construct_valuemap(kiara_api=self.api, values={})

        if not max_columns:
            num_columns = len(fields)
        else:
            if len(fields) >= max_columns:
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
            _key = f"op_input_{key}_{field_name}_req"
            comp: InputComponent = self.kiara.get_input_component(data_type_name)

            column_idx = idx % num_columns
            input_opts = InputOptions(
                key=_key, label=field_name, value_schema=schema, help=help
            )
            r = comp.render_input_field(columns[column_idx], input_opts)

            values[field_name] = r

        result = construct_valuemap(kiara_api=self.api, values=values)
        return result

    def render_default(
        self,
        st: DeltaGenerator,
        key: str,
        fields: Mapping[str, ValueSchema],
        options: AssemblyOptions,
    ) -> ValueMap:

        required: Dict[str, ValueSchema] = {}
        optional: Dict[str, ValueSchema] = {}
        max_columns = options.max_columns

        optional_expanded = True

        for input_name, input_schema in fields.items():
            if input_schema.is_required():
                required[input_name] = input_schema
            else:
                optional[input_name] = input_schema

        values = {}
        if required:
            if not max_columns:
                num_columns = len(required)
            else:
                if len(required) >= max_columns:
                    num_columns = max_columns
                else:
                    num_columns = len(required)

            columns = st.columns(num_columns)
            for idx, field_name in enumerate(required.keys()):
                schema = required[field_name]
                help = None
                if schema.doc.is_set:
                    help = schema.doc.full_doc
                data_type_name = schema.type
                _key = f"op_input_{key}_{field_name}_req"
                comp = self.kiara.get_input_component(data_type_name)

                column_idx = idx % num_columns
                input_opts = InputOptions(
                    key=_key, label=field_name, value_schema=schema, help=help
                )

                r = comp.render_input_field(columns[column_idx], input_opts)

                values[field_name] = r

        if optional:
            opt_expander = st.expander("Optional inputs", expanded=optional_expanded)

            if not max_columns:
                num_columns = len(optional)
            else:
                if len(optional) >= max_columns:
                    num_columns = max_columns
                else:
                    num_columns = len(optional)

            opt_columns = opt_expander.columns(num_columns)

            for idx, field_name in enumerate(optional.keys()):
                schema = optional[field_name]
                # desc = schema.doc.description
                # doc = schema.doc.doc
                help = None
                if schema.doc.is_set:
                    help = schema.doc.full_doc

                if idx >= num_columns:
                    if idx % num_columns == 0:
                        # opt_expander.markdown("---")
                        opt_columns = opt_expander.columns(num_columns)

                data_type_name = schema.type
                _key = f"op_input_{key}_{field_name}_opt"
                comp = self.kiara.get_input_component(data_type_name)
                column_idx = idx % num_columns
                input_opts = InputOptions(
                    key=_key, label=field_name, value_schema=schema, help=help
                )

                r = comp.render_input_field(opt_columns[column_idx], input_opts)
                values[field_name] = r
        result = construct_valuemap(kiara_api=self.api, values=values)
        return result


class OperationInputsOptions(AssemblyOptions):
    operation_id: str = Field(
        description="The id of the operation to render the inputs for."
    )


class OperationInputs(InputAssemblyComponent):

    _component_name = "operation_inputs"
    _options = OperationInputsOptions  # type: ignore

    def get_input_fields(
        self, options: OperationInputsOptions
    ) -> Mapping[str, ValueSchema]:

        # TODO: check argument
        op = self.api.get_operation(options.operation_id)
        return op.inputs_schema


class InputFieldsOptions(AssemblyOptions):
    fields: Mapping[str, ValueSchema] = Field(description="The fields to render.")


class InputFields(InputAssemblyComponent):

    _component_name = "input_fields"
    _options = InputFieldsOptions  # type: ignore

    def get_input_fields(
        self, options: InputFieldsOptions
    ) -> Mapping[str, ValueSchema]:
        return options.fields
