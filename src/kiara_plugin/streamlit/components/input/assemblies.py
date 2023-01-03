# -*- coding: utf-8 -*-
import abc
from typing import Dict, Mapping

from kiara import ValueMap, ValueSchema
from kiara.utils.values import construct_valuemap
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.defaults import PROFILE_KEYWORD


class InputAssemblyComponent(KiaraComponent):
    @abc.abstractmethod
    def get_input_fields(self, *args, **kwargs) -> Mapping[str, ValueSchema]:
        pass

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        profile = kwargs.pop(PROFILE_KEYWORD, "default")

        method_name = f"render_{profile}"
        if not hasattr(self, method_name):
            raise Exception(f"No input fields render profile '{profile}' available.'")

        fields = self.get_input_fields(*args, **kwargs)
        func = getattr(self, method_name, fields)
        return func(st, key, fields, *args, **kwargs)

    def render_default(
        self,
        st: DeltaGenerator,
        key: str,
        fields: Mapping[str, ValueSchema],
        *args,
        **kwargs,
    ) -> ValueMap:

        required: Dict[str, ValueSchema] = {}
        optional: Dict[str, ValueSchema] = {}
        max_columns = kwargs.pop("max_columns", 4)

        for input_name, input_schema in fields.items():
            if input_schema.is_required():
                required[input_name] = input_schema
            else:
                optional[input_name] = input_schema

        if not max_columns:
            num_columns = len(required)
        else:
            if len(required) >= max_columns:
                num_columns = max_columns
            else:
                num_columns = len(required)

        columns = st.columns(num_columns)
        values = {}
        for idx, field_name in enumerate(required.keys()):
            schema = required[field_name]
            help = None
            if schema.doc.is_set:
                help = schema.doc.full_doc
            data_type_name = schema.type
            _key = f"op_input_{key}_{field_name}_req"
            comp = self.kiara.get_input_component(data_type_name)

            column_idx = idx % num_columns
            r = comp.render_input_field(
                columns[column_idx], _key, field_name, help=help
            )

            values[field_name] = r

        if optional:
            opt_expander = st.expander("Optional inputs")

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

                data_type_name = schema.type
                _key = f"op_input_{key}_{field_name}_opt"
                comp = self.kiara.get_input_component(data_type_name)
                column_idx = idx % num_columns
                r = comp.render_input_field(
                    opt_columns[column_idx], _key, field_name, help=help
                )
                values[field_name] = r
        result = construct_valuemap(kiara=self.api, values=values)
        return result


class OperationInputs(InputAssemblyComponent):

    _component_name = "operation_inputs"

    def get_input_fields(self, *args, **kwargs) -> Mapping[str, ValueSchema]:
        op_name = None
        if "operation" in kwargs.keys():
            op_name = kwargs["operation"]
        if not op_name and args:
            op_name = args[0]

        # TODO: check argument
        op = self.api.get_operation(op_name)
        return op.inputs_schema
