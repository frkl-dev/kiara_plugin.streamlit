# -*- coding: utf-8 -*-
import abc
import copy
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    TypeVar,
    Union,
)

from pydantic import Field

from kiara.api import Value, ValueSchema
from kiara.defaults import DEFAULT_NO_DESC_VALUE, SpecialValue
from kiara.registries.data import ValueLink
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.modals import (
    ModalConfig,
    ModalRequest,
    ModalResult,
)
from kiara_plugin.streamlit.defaults import (
    NO_LABEL_MARKER,
    NO_VALUE_MARKER,
    WANTS_MODAL_MARKER_KEY,
)

if TYPE_CHECKING:
    from kiara_plugin.streamlit import KiaraStreamlit
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class InputOptions(ComponentOptions):

    display_style: str = Field(
        description="The display style to use for this input field.", default="default"
    )
    smart_label: bool = Field(
        description="Whether to try to shorten the label.", default=True
    )
    help: Union[str, None] = Field(
        description="The help to display for this input field.",
        default=DEFAULT_NO_DESC_VALUE,
    )
    label: str = Field(
        description="The label to use for the input field.", default=NO_LABEL_MARKER
    )
    value_schema: Union[None, ValueSchema] = Field(
        description="The schema for the value in question.", default=None
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
    def get_data_type(cls) -> Union[str, None]:
        """Return the 'kiara' data type name this input component can handle.

        This is used to dynamically register and auto-generate components on the
        root 'KiaraStreamlit' instance. If 'None' is returned, the component will
        be ignored in the registration process but can still be used manually.
        """

    @classmethod
    def get_input_profile(cls) -> str:
        return "default"

    @classmethod
    def get_default_label(cls) -> str:
        if cls.get_data_type() in ["any", None]:
            return "Select value"
        else:
            return f"Select {cls.get_data_type()} value"

    @abc.abstractmethod
    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: INPUT_OPTIONS_TYPE,
    ) -> Union[ValueLink, None, str, uuid.UUID]:
        pass

    def _render(
        self, st: "KiaraStreamlitAPI", options: INPUT_OPTIONS_TYPE
    ) -> Union[Value, None]:

        if options.label == NO_LABEL_MARKER:
            options.label = self.get_default_label()

        value = self.render_input_field(st, options=options)
        if not value:
            return None
        else:
            return self.api.get_value(value)  # type: ignore


class DefaultInputOptions(InputOptions):

    add_no_value_option: bool = Field(
        description="Add an option so the user can chose to select no value. This is overwritten by a potential value_schema (if supplied).",
        default=False,
    )
    value_has_alias: bool = Field(
        description="Whether the values to present need to have a registered alias.",
        default=True,
    )
    show_preview: Union[bool, None] = Field(
        description="Whether to show a preview of the value. If not provided, a selectbox will be rendered so the user can choose.",
        default=None,
    )
    display_value_type: Union[bool, None] = Field(
        description="Whether to display the data type in the list. By default it hides it for a single 'data type' option, and shows for multiple.",
        default=None,
    )
    data_type: Union[str, List[str], None] = Field(
        description="The data type(s) to display as selection.", default=None
    )
    add_import_widget: Union[str, None, bool] = Field(
        description="The name of a widget that can be used to create a new value. If specified, a 'Create' button is added that calls that widget. If 'True', the widget will be chosen automatically, if a string, the component with that name will be used.",
        default=None,
    )


class ImportResult(ModalResult):
    value: Union[Value, None] = Field(
        description="The value that was imported.", default=None
    )
    alias: Union[str, None] = Field(
        description="The alias that was used to store the value.", default=None
    )


class DefaultInputComponent(InputComponent):
    """Render a selectbox with all available values (for a specific type, if applicable)."""

    _component_name = "select_value"
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
        st: "KiaraStreamlitAPI",
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
            # here we use the instance of the input component for the data type that was auto generated, if available.
            # it will nonetheless continue below, just a differently configured instance (unless there is a custom input widget for that data type)
            dt = data_types[0]
            inp_comp = self.kiara_streamlit.get_input_component(dt)
            if inp_comp and inp_comp.__class__ != self.__class__:
                copy_options = options.copy()
                _key_selectbox = f"{_key}_value_select_{_key}"
                copy_options.key = _key_selectbox
                return inp_comp.render_input_field(st, options=copy_options)

        if not options.add_import_widget:
            result: Union[str, None] = self._render_default_selectbox(
                st, options, data_types=data_types
            )
            return result
        else:

            if len(data_types) > 1:
                raise Exception(
                    "Cannot use 'add_create_widget' when multiple data types are specified."
                )

            data_type = data_types[0]

            columns = st.columns([5, 1])
            result, select_box_key = self._render_default_selectbox(st=columns[0], options=options, data_types=data_types, label=f"Select existing {data_type} value", also_return_key=True)  # type: ignore
            columns[1].header("")

            import_comp = st.kiara.get_import_component(data_type)
            if import_comp is None:
                help = f"No import component available for data type '{data_type}'. Contact the developers and ask them to implement one."
            else:
                help = f"Import (or create) a new value of type '{data_type}'."
            create_widget = columns[1].button(
                f"Import {data_type}",
                disabled=not import_comp,
                help=help,
                key=f"{_key}_import_button",
            )
            if create_widget:
                modal_result = ImportResult()
                modal_config = ModalConfig(store_alias_key=select_box_key)
                modal_request = ModalRequest(
                    modal=import_comp, config=modal_config, result=modal_result
                )
                st.session_state[WANTS_MODAL_MARKER_KEY].append(modal_request)  # type: ignore
                st.experimental_rerun()

            return result

    def _render_default_selectbox(
        self,
        st: "KiaraStreamlitAPI",
        options: DefaultInputOptions,
        data_types: List[str],
        label: Union[str, None] = None,
        also_return_key: bool = False,
    ) -> Any:

        has_alias = options.value_has_alias
        if has_alias:
            available_values = self.api.list_aliases(data_types=list(data_types))
        else:
            available_values = self.api.list_values(
                data_types=list(data_types), has_alias=False
            )

        default = None

        if options.value_schema:
            if options.value_schema.default not in [
                SpecialValue.NO_VALUE,
                SpecialValue.NOT_SET,
                None,
            ]:
                default = options.value_schema.default
            optional = options.value_schema.optional
        else:
            optional = options.add_no_value_option

        display_type = options.display_value_type
        if display_type is None and len(data_types) != 1:
            display_type = True
        elif display_type is None:
            display_type = False

        format_func: Callable = str
        if display_type:

            def format_func(v: Any) -> str:
                if v == NO_VALUE_MARKER:
                    return v  # type: ignore
                return f"{v} ({available_values[v].data_type_name})"

        if optional:
            _item_options = [NO_VALUE_MARKER, *available_values.keys()]
            if not default:
                default = NO_VALUE_MARKER
        else:
            _item_options = list(available_values.keys())

        callback, _select_key = self._create_session_store_callback(
            options, "input", "value", "select", default=default
        )

        if label is None:
            label = options.label

        result = st.selectbox(
            label=label,
            options=_item_options,
            key=_select_key,
            format_func=format_func,
            on_change=callback,
            help=options.help,
        )
        if result == NO_VALUE_MARKER:
            result = None

        if options.show_preview is None:
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
        elif options.show_preview is True:
            # TODO: support preview profiles
            if result is not None:
                _key = options.create_key("preview", result)
                comp = self.get_component("preview")
                if hasattr(st, "__enter__"):
                    with st:
                        comp.render_func(st)(key=_key, value=result)
                else:
                    comp.render_func(st)(key=_key, value=result)

        if not also_return_key:
            return result
        else:
            return result, _select_key


class PickValueInputOptions(InputOptions):

    display_value_type: Union[bool, None] = Field(
        description="Whether to display the data type in the list. By default it hides it for a single 'data type' option, and shows for multiple.",
        default=None,
    )
    show_preview: Union[None, bool] = Field(
        description="Whether to show a preview of the value. If not provided, a selectbox will be rendered so the user can choose.",
        default=None,
    )
    values: Mapping[str, Value] = Field(description="The values to pick from.")


class PickValueComponent(InputComponent):
    """Render a selectbox with the provided all the values in the provided value map."""

    _component_name = "pick_value"
    _options = PickValueInputOptions  # type: ignore

    @classmethod
    def get_data_type(cls) -> Union[str, None]:
        return None

    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: PickValueInputOptions,
    ) -> Union[ValueLink, None, str, uuid.UUID]:

        if options.smart_label:
            options.label = options.label.split("__")[-1]

        data_types = []

        for name, value in options.values.items():
            data_type = value.data_type_name
            if data_type not in data_types:
                data_types.append(value.data_type_name)

        result: Union[str, None] = self._render_default_selectbox(
            st, options, data_types=data_types
        )
        return result

    def _render_default_selectbox(
        self,
        st: "KiaraStreamlitAPI",
        options: PickValueInputOptions,
        data_types: List[str],
    ):

        available_values = options.values

        display_type = options.display_value_type
        if display_type is None and len(data_types) != 1:
            display_type = True
        elif display_type is None:
            display_type = False

        format_func: Callable = str
        if display_type:

            def format_func(v: Any) -> str:
                if v == NO_VALUE_MARKER:
                    return v  # type: ignore
                return f"{v} ({available_values[v].data_type_name})"

        _item_options = list(available_values.keys())

        # if _item_options:
        #     default = _item_options[0]
        # else:
        #     default = None

        callback, _select_key = self._create_session_store_callback(
            options, "input", "pick", "value"
        )

        result = st.selectbox(
            label=options.label,
            options=_item_options,
            key=_select_key,
            format_func=format_func,
            on_change=callback,
            help=options.help,
        )

        if options.show_preview is None:
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
        elif options.show_preview is True:
            # TODO: support preview profiles
            if result is not None:
                _key = options.create_key("preview", result)
                comp = self.get_component("preview")
                if hasattr(st, "__enter__"):
                    with st:
                        comp.render_func(st)(key=_key, value=result)
                else:
                    comp.render_func(st)(key=_key, value=result)

        return result
