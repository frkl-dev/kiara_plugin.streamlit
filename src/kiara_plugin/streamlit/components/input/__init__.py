# -*- coding: utf-8 -*-
import abc
import copy
import uuid
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, TypeVar, Union

from kiara import Value, ValueSchema
from kiara.defaults import SpecialValue
from kiara.registries.data import ValueLink
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.defaults import NO_LABEL_MARKER, NO_VALUE_MARKER

if TYPE_CHECKING:
    from kiara_plugin.streamlit import KiaraStreamlit


class InputOptions(ComponentOptions):

    label: str = Field(
        description="The label to use for the input field.", default=NO_LABEL_MARKER
    )
    smart_label: bool = Field(
        description="Whether to try to shorten the label.", default=True
    )
    value_schema: Union[None, ValueSchema] = Field(
        description="The schema for the value in question."
    )
    help: Union[str, None] = Field(
        description="The help to display for this input field."
    )
    display_style: str = Field(
        description="The display style to use for this input field.", default="default"
    )

    def get_default(self) -> Any:
        if self.value_schema is None:
            return None
        return copy.deepcopy(self.value_schema.default)


INPUT_OPTIONS_TYPE = TypeVar("INPUT_OPTIONS_TYPE", bound=InputOptions)


class InputComponent(KiaraComponent[INPUT_OPTIONS_TYPE]):

    _options = InputOptions  # type: ignore

    @classmethod
    @abc.abstractmethod
    def get_data_type(cls) -> str:
        pass

    @classmethod
    def get_input_profile(cls) -> str:
        return "default"

    @classmethod
    def get_default_label(cls) -> str:
        if cls.get_data_type() == "any":
            return "Select value"
        else:
            return f"Select {cls.get_data_type()} value"

    @abc.abstractmethod
    def render_input_field(
        self,
        st: DeltaGenerator,
        options: INPUT_OPTIONS_TYPE,
    ) -> Union[ValueLink, None, str, uuid.UUID]:
        pass

    def _render(
        self, st: DeltaGenerator, options: INPUT_OPTIONS_TYPE
    ) -> Union[Value, None]:

        if options.label == NO_LABEL_MARKER:
            options.label = self.get_default_label()

        value = self.render_input_field(st, options=options)
        if not value:
            return None
        else:
            return self.api.get_value(value)


class DefaultInputOptions(InputOptions):

    data_types: Union[str, List[str], None] = Field(
        description="The data types to display as selection.", default=None
    )
    value_has_alias: bool = Field(
        description="Whether the values to present need to have a registered alias.",
        default=True,
    )
    display_value_type: Union[bool, None] = Field(
        description="Whether to display the data type in the list.", default=None
    )
    preview: str = Field(
        description="The preview to use for the value.", default="auto"
    )


class DefaultInputComponent(InputComponent):

    _component_name = "value_input"
    _options = DefaultInputOptions  # type: ignore

    def __init__(
        self,
        kiara_streamlit: "KiaraStreamlit",
        data_types: Union[str, Iterable[str], None] = None,
    ):

        if data_types:
            if isinstance(data_types, str):
                data_types = [data_types]

        self._data_types: Union[None, Iterable[str]] = data_types
        super().__init__(kiara_streamlit=kiara_streamlit)

    @classmethod
    def get_data_type(cls) -> str:
        return "any"

    def render_input_field(
        self,
        st: DeltaGenerator,
        options: DefaultInputOptions,
    ) -> Union[ValueLink, None, str, uuid.UUID]:

        if options.smart_label:
            options.label = options.label.split("__")[-1]

        if options.data_types is None:
            data_types: List[str] = []
        elif isinstance(options.data_types, str):
            data_types = [options.data_types]
        else:
            data_types = options.data_types

        if self._data_types and data_types:
            raise Exception("'data_types' argument not allowed for this component.")

        if not data_types:
            if self._data_types is None:
                data_types = []
            else:
                data_types = list(self._data_types)

        if not data_types:
            data_types.append(self.get_data_type())

        _key = options.create_key(*sorted(data_types))
        _key_selectbox = f"{_key}_value_select_{_key}"

        if len(data_types) == 1:
            dt = data_types[0]
            inp_comp = self.kiara.get_input_component(dt)
            if inp_comp and inp_comp.__class__ != self.__class__:
                copy_options = options.copy()
                copy_options.key = _key_selectbox
                return inp_comp.render_input_field(st, options=copy_options)

        has_alias = options.value_has_alias
        available_values = self.api.list_aliases(
            data_types=list(data_types), has_alias=has_alias
        )

        optional = False
        default = None
        if options.value_schema:
            if options.value_schema.default not in [
                SpecialValue.NO_VALUE,
                SpecialValue.NOT_SET,
                None,
            ]:
                default = options.value_schema.default
            optional = options.value_schema.optional

        display_type = options.display_value_type
        format_func: Callable = str
        if len(data_types) != 1 and (display_type is None or display_type):

            def format_func(v: Any) -> str:
                if v == NO_VALUE_MARKER:
                    return v
                return f"{v} ({available_values[v].data_type_name})"

        if optional:
            _item_options = [NO_VALUE_MARKER] + list(available_values.keys())
        else:
            _item_options = list(available_values.keys())

        idx = 0
        if default is not None and default in options:
            idx = _item_options.index(default)

        with_preview = options.preview

        if with_preview == "auto":
            with_preview = "checkbox"

        if not with_preview or with_preview.lower() in ["false", "no"]:
            result = st.selectbox(
                label=options.label,
                options=_item_options,
                key=_key_selectbox,
                format_func=format_func,
                index=idx,
            )
        else:

            result = st.selectbox(
                label=options.label,
                options=_item_options,
                key=_key_selectbox,
                format_func=format_func,
                index=idx,
            )
            if result == NO_VALUE_MARKER:
                result = None
            if with_preview == "checkbox":
                _key = options.create_key("preview", result)
                if result is None:
                    disabled = True
                else:
                    disabled = False
                show_preview = st.checkbox(
                    "Preview", key=f"preview_{_key_selectbox}", disabled=disabled
                )
                if show_preview:
                    comp = self.get_component("preview")
                    if hasattr(st, "__enter__"):
                        with st:
                            comp.render_func(st)(key=_key, value=result)
                    else:
                        comp.render_func(st)(key=_key, value=result)
            elif with_preview:
                if result is not None:
                    _key = options.create_key("preview", result)
                    comp = self.get_component("preview")
                    if hasattr(st, "__enter__"):
                        with st:
                            comp.render_func(st)(key=_key, value=result)
                    else:
                        comp.render_func(st)(key=_key, value=result)

        return result
