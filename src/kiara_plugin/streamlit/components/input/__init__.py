# -*- coding: utf-8 -*-
import abc
import copy
import uuid
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Tuple, TypeVar, Union

from kiara.api import Value, ValueSchema
from kiara.defaults import SpecialValue
from kiara.registries.data import ValueLink
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.defaults import NO_LABEL_MARKER, NO_VALUE_MARKER

if TYPE_CHECKING:
    from kiara_plugin.streamlit.streamlit import KiaraStreamlit


class InputOptions(ComponentOptions):

    display_style: str = Field(
        description="The display style to use for this input field.", default="default"
    )
    smart_label: bool = Field(
        description="Whether to try to shorten the label.", default=True
    )
    label: str = Field(
        description="The label to use for the input field.", default=NO_LABEL_MARKER
    )
    help: Union[str, None] = Field(
        description="The help to display for this input field."
    )
    value_schema: Union[None, ValueSchema] = Field(
        description="The schema for the value in question."
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
            return self.api.get_value(value)  # type: ignore

    def _create_session_store_callback(
        self, options: ComponentOptions, *key, default=None
    ) -> Tuple[Callable, str]:

        _widget_key = options.create_key(*key)

        current = self.get_session_var(options, *key, default=default)

        if current is not None and _widget_key not in self._session_state:
            self._session_state[_widget_key] = current

        def callback():
            self._st.session_state[
                options.get_session_key(*key)
            ] = self._st.session_state[_widget_key]

        return callback, _widget_key


class DefaultInputOptions(InputOptions):

    value_has_alias: bool = Field(
        description="Whether the values to present need to have a registered alias.",
        default=True,
    )
    preview: str = Field(
        description="The preview to use for the value.", default="auto"
    )
    display_value_type: Union[bool, None] = Field(
        description="Whether to display the data type in the list.", default=None
    )
    data_type: Union[str, List[str], None] = Field(
        description="The data type(s) to display as selection.", default=None
    )


class DefaultInputComponent(InputComponent):
    """Render a selectbox with all available values (for a specific type, if applicable)."""

    _component_name = "value_input"
    _options = DefaultInputOptions  # type: ignore

    def __init__(
        self,
        kiara_streamlit: "KiaraStreamlit",
        component_name: str,
        data_types: Union[str, Iterable[str], None] = None,
        doc: Any = None,
    ):

        if data_types:
            if isinstance(data_types, str):
                data_types = [data_types]

        self._data_types: Union[None, Iterable[str]] = data_types
        super().__init__(
            kiara_streamlit=kiara_streamlit, component_name=component_name, doc=doc
        )

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

        if options.data_type is None:
            data_types: List[str] = []
        elif isinstance(options.data_type, str):
            data_types = [options.data_type]
        else:
            data_types = options.data_type

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

        if len(data_types) == 1:
            dt = data_types[0]
            inp_comp = self.kiara_streamlit.get_input_component(dt)
            if inp_comp and inp_comp.__class__ != self.__class__:
                copy_options = options.copy()
                _key_selectbox = f"{_key}_value_select_{_key}"
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
        if display_type is None and data_types != 1:
            display_type = True
        elif display_type is None:
            display_type = False

        format_func: Callable = str
        if display_type:

            def format_func(v: Any) -> str:
                if v == NO_VALUE_MARKER:
                    return v
                return f"{v} ({available_values[v].data_type_name})"

        if optional:
            _item_options = [NO_VALUE_MARKER] + list(available_values.keys())
            if not default:
                default = NO_VALUE_MARKER
        else:
            _item_options = list(available_values.keys())

        with_preview = options.preview

        if with_preview == "auto":
            with_preview = "checkbox"

        callback, _select_key = self._create_session_store_callback(
            options, "input", "value", "select", default=default
        )

        if not with_preview or with_preview.lower() in ["false", "no"]:
            result = st.selectbox(
                label=options.label,
                options=_item_options,
                key=_select_key,
                format_func=format_func,
                on_change=callback,
                help=options.help,
            )
        else:
            result = st.selectbox(
                label=options.label,
                options=_item_options,
                key=_select_key,
                format_func=format_func,
                on_change=callback,
                help=options.help,
            )
            if result == NO_VALUE_MARKER:
                result = None
            if with_preview == "checkbox":
                if result:
                    _key = options.create_key("preview", result)
                else:
                    _key = options.create_key("preview", "no_value")
                if result is None:
                    disabled = True
                else:
                    disabled = False
                show_preview = st.checkbox(
                    "Preview", key=f"preview_{_select_key}", disabled=disabled
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
