# -*- coding: utf-8 -*-
import abc
from typing import Any

from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components.input import InputComponent, InputOptions


class ScalarInput(InputComponent):
    @classmethod
    def get_default_label(cls) -> str:
        return "Provide value"

    def render_input_field(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):
        if options.smart_label:
            options.label = options.label.split("__")[-1]

        scalar = self.render_scalar_input(st, options=options)
        if scalar is None:
            return None
        value = self.api.register_data(scalar, data_type=self.get_data_type())
        return value

    @abc.abstractmethod
    def render_scalar_input(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ) -> Any:
        pass


class BooleanInput(ScalarInput):

    _component_name = "input_boolean"

    @classmethod
    def get_data_type(cls) -> str:
        return "boolean"

    @classmethod
    def get_default_label(cls) -> str:
        return "Check enabled"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):

        inp = st.checkbox(
            label=options.label, key=options.key, value=options.get_default()
        )
        return inp


class StringInput(ScalarInput):

    _component_name = "input_string"

    @classmethod
    def get_data_type(cls) -> str:
        return "string"

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter text"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):

        txt = st.text_input(
            label=options.label, key=options.key, value=options.get_default()
        )
        return txt


class IntegerInput(ScalarInput):

    _component_name = "input_integer"

    @classmethod
    def get_data_type(cls) -> str:
        return "integer"

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter integer"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):

        style = options.display_style
        if not style:
            style = "default"

        default = options.get_default()
        if default is None:
            default = 0
        else:
            default = int(default)

        if style == "default":
            number = st.number_input(
                label=options.label, key=options.key, value=default
            )
        elif style == "text_input":
            number_str = st.text_input(
                label=options.label, key=options.key, value=str(default)
            )
            try:
                number = int(number_str)
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

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter float"

    def render_scalar_input(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):

        style = options.display_style
        if not style:
            style = "default"

        default = options.get_default()
        if default is None:
            default = 0.0
        else:
            default = float(default)

        if style == "default":
            number = st.number_input(
                label=options.label, key=options.key, value=default
            )
        elif style == "text_input":
            number_str = st.text_input(
                label=options.label, key=options.key, value=str(default)
            )
            try:
                number = float(number_str)
            except Exception:
                number = None
        else:
            raise Exception(f"Invalid style argument: {style}.")

        return number