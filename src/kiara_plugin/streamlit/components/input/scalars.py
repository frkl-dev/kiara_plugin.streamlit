# -*- coding: utf-8 -*-
import abc
from typing import Union

from kiara import ValueSchema
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components.input import InputComponent
from kiara_plugin.streamlit.defaults import PROFILE_KEYWORD


class ScalarInput(InputComponent):
    def get_default_label(cls) -> str:
        return "Provide value"

    def render_input_field(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: Union[ValueSchema, None],
        *args,
        **kwargs,
    ):

        label = label.split("__")[-1]
        scalar = self.render_scalar_input(st, key, label, schema, *args, **kwargs)
        if scalar is None:
            return None
        value = self.api.register_data(scalar, data_type=self.get_data_type())
        return value

    @abc.abstractmethod
    def render_scalar_input(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: Union[ValueSchema, None],
        *args,
        **kwargs,
    ) -> any:
        pass


class BooleanInput(ScalarInput):

    _component_name = "input_boolean"

    @classmethod
    def get_data_type(cls) -> str:
        return "boolean"

    def get_default_label(cls) -> str:
        return "Check enabled"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: ValueSchema,
        *args,
        **kwargs,
    ):

        if "value" not in kwargs.keys():
            value = schema and schema.default is True
        else:
            value = kwargs["value"]

        inp = st.checkbox(label=label, key=key, value=value, **kwargs)
        return inp


class StringInput(ScalarInput):

    _component_name = "input_string"

    @classmethod
    def get_data_type(cls) -> str:
        return "string"

    def get_default_label(cls) -> str:
        return "Enter text"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: Union[ValueSchema, None],
        *args,
        **kwargs,
    ):

        if "value" not in kwargs.keys():
            if schema and isinstance(schema.default, str):
                value = schema.default
            else:
                value = ""
        else:
            value = kwargs["value"]

        txt = st.text_input(label=label, key=key, value=value, **kwargs)
        return txt


class IntegerInput(ScalarInput):

    _component_name = "input_integer"

    @classmethod
    def get_data_type(cls) -> str:
        return "integer"

    def get_default_label(cls) -> str:
        return "Enter integer"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: Union[ValueSchema, None],
        *args,
        **kwargs,
    ):

        style = kwargs.pop(PROFILE_KEYWORD, None)
        if not style:
            style = "default"

        default = kwargs.pop("value", None)
        if default is None:
            if schema and isinstance(schema.default, int):
                default = schema.default
            else:
                default = 0
        else:
            default = int(default)

        if style == "default":
            number = st.number_input(label=label, key=key, value=default, **kwargs)
        elif style == "text_input":
            value = str(default)
            number = st.text_input(label=label, key=key, value=value, **kwargs)
            try:
                number = int(number)
            except Exception:
                number = None
        else:
            raise Exception(f"Invalid style argument: {style}.")

        return number


class FloatInput(ScalarInput):

    _component_name = "input_float"

    @classmethod
    def get_data_type(cls) -> str:
        return "float"

    def get_default_label(cls) -> str:
        return "Enter float"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        key: str,
        label: str,
        schema: Union[ValueSchema, None],
        *args,
        **kwargs,
    ):

        style = kwargs.pop("style", None)
        if not style:
            style = "default"

        default = kwargs.pop("value", None)
        if default is None:
            if schema and isinstance(schema.default, float):
                default = schema.default
            else:
                default = 0.0
        else:
            default = float(default)

        if style == "default":
            number = st.number_input(label=label, key=key, value=default, **kwargs)
        elif style == "text_input":
            value = str(default)
            number = st.text_input(label=label, key=key, value=value, **kwargs)
            try:
                number = int(number)
            except Exception:
                number = None
        else:
            raise Exception(f"Invalid style argument: {style}.")

        return number
