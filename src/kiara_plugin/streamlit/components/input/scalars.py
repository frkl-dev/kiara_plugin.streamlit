# -*- coding: utf-8 -*-
import abc
from typing import TYPE_CHECKING, Any

from kiara.defaults import SpecialValue
from kiara.exceptions import KiaraException
from kiara_plugin.streamlit.components.input import InputComponent, InputOptions

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ScalarInput(InputComponent):
    @classmethod
    def get_default_label(cls) -> str:
        return "Provide value"

    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):
        if options.smart_label:
            options.label = options.label.split("__")[-1]

        scalar = self.render_scalar_input(st, options=options)
        if scalar is None:
            return None
        value = self.api.register_data(
            scalar, data_type=self.get_data_type(), reuse_existing=True
        )
        return value

    @abc.abstractmethod
    def render_scalar_input(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ) -> Any:
        pass


class BooleanInput(ScalarInput):
    """Render a checkbox for a boolean input."""

    _component_name = "input_boolean"
    _examples = [
        {"doc": "A simple boolean input.", "args": {"label": "Should I?"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "boolean"

    @classmethod
    def get_default_label(cls) -> str:
        return "Check enabled"

    def render_scalar_input(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):
        default = options.get_default()

        if options.value_schema and options.value_schema.optional:
            if default in [None, SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
                default = None
            else:
                default = bool(default)

            callback, _key = self._create_session_store_callback(
                options,
                "input",
                "scalar",
                "radio",
                self.__class__.get_data_type(),
                default=default,
            )

            choices = ["auto", "true", "false"]
            if default is None:
                idx = 0
            elif default:
                idx = 1
            else:
                idx = 2

            result = st.radio(
                label=options.label,
                options=choices,
                index=idx,
                key=_key,
                help=options.help,
                on_change=callback,
                horizontal=True,
            )
            if result == "auto":
                inp = None
            elif result == "true":
                inp = True
            else:
                inp = False
        else:
            if default in [None, SpecialValue.NO_VALUE, SpecialValue.NOT_SET]:
                default = False
            else:
                default = bool(default)

            callback, _key = self._create_session_store_callback(
                options,
                "input",
                "scalar",
                "checkbox",
                self.__class__.get_data_type(),
                default=default,
            )

            inp = st.checkbox(
                label=options.label, key=_key, help=options.help, on_change=callback
            )
        return inp


class StringInput(ScalarInput):
    """Render a text input widget."""

    _component_name = "input_string"
    _examples = [
        {"doc": "A simple text field input.", "args": {"label": "Say somthing"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "string"

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter text"

    def render_scalar_input(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):

        default = options.get_default()
        if default in [None, SpecialValue.NOT_SET, SpecialValue.NO_VALUE]:
            default = ""

        callback, _key = self._create_session_store_callback(
            options, "input", "scalar", self.__class__.get_data_type(), default=default
        )

        txt = st.text_input(
            label=options.label, key=_key, help=options.help, on_change=callback
        )
        return txt


class IntegerInput(ScalarInput):
    """Render an integer input widget.

    You can select between two different styles:
    - "default": a number input widget
    - "text_input": a text input widget, which will be converted to an integer
    """

    _component_name = "input_integer"
    _examples = [
        {"doc": "A simple integer input.", "args": {"label": "Select an integer."}},
        {
            "doc": "A text field to provide an interger.",
            "args": {"label": "Enter a number.", "display_style": "text_input"},
        },
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "integer"

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter integer"

    def render_scalar_input(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):

        default = options.get_default()
        if default in [None, SpecialValue.NOT_SET, SpecialValue.NO_VALUE]:
            default = int(0)
        else:
            default = int(default)

        style = options.display_style
        if not style:
            style = "default"

        if style == "text_input":
            default = str(default)

        callback, _key = self._create_session_store_callback(
            options, "input", "scalar", self.__class__.get_data_type(), default=default
        )

        if style == "default":
            number = st.number_input(
                label=options.label,
                key=f"{_key}__default",
                help=options.help,
                on_change=callback,
                step=1,
            )

        elif style == "text_input":
            number_str = st.text_input(
                label=options.label,
                key=f"{_key}__text_input",
                on_change=callback,
                help=options.help,
            )
            if not number_str:
                return None
            try:
                number = int(number_str)
            except Exception:
                raise KiaraException(f"Can't parse input as integer: {number_str}.")
        else:
            raise Exception(f"Invalid style argument: {style}.")

        return number


class FloatInput(ScalarInput):
    """Render an input widget for a floating point number.

    You can select between two different styles:
    - "default": a number input widget
    - "text_input": a text input widget, which will be converted to an integer
    """

    _component_name = "input_float"
    _examples = [
        {"doc": "A simple float input.", "args": {"label": "Select a float."}},
        {
            "doc": "A text field to provide an interger.",
            "args": {"label": "Enter a float.", "display_style": "text_input"},
        },
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "float"

    @classmethod
    def get_default_label(cls) -> str:
        return "Enter float"

    def render_scalar_input(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):

        default = options.get_default()
        if default in [None, SpecialValue.NOT_SET, SpecialValue.NO_VALUE]:
            default = 0.0
        else:
            default = float(default)

        style = options.display_style
        if not style:
            style = "default"

        if style == "text_input":
            default = str(default)

        callback, _key = self._create_session_store_callback(
            options, "input", "scalar", self.__class__.get_data_type(), default=default
        )

        if style == "default":
            number = st.number_input(
                label=options.label,
                key=f"{_key}_number_input",
                on_change=callback,
                help=options.help,
                step=1.0,
            )
        elif style == "text_input":
            number_str = st.text_input(
                label=options.label,
                key=f"{_key}_text_field",
                on_change=callback,
                help=options.help,
            )
            if not number_str:
                return None
            try:
                number = float(number_str)
            except Exception:
                raise KiaraException(f"Can't parse input as float: {number_str}")
        else:
            raise Exception(f"Invalid style argument: {style}.")

        return number
