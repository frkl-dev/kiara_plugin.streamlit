# -*- coding: utf-8 -*-
import abc
import uuid
from typing import TYPE_CHECKING, Iterable, Union

from streamlit.delta_generator import DeltaGenerator, Value

from kiara_plugin.streamlit.components import KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit import KiaraStreamlit


class InputComponent(KiaraComponent):
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
        self, st: DeltaGenerator, key: str, label: str, *args, **kwargs
    ):
        pass

    def _render(
        self, st: DeltaGenerator, key: str, *args, **kwargs
    ) -> Union[Value, None]:

        label = kwargs.pop("label", None)
        if label is None:
            label = self.get_default_label()

        value = self.render_input_field(st, key, label, *args, **kwargs)
        if not value:
            return None

        return self.api.get_value(value)


class DefaultInputComponent(InputComponent):

    _component_name = "value_input"

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
        self, st: DeltaGenerator, key: str, label: str, *args, **kwargs
    ) -> Union[Value, None, str, uuid.UUID]:

        data_types = set(kwargs.pop("data_types", []))
        data_type = kwargs.pop("data_type", None)
        if data_type:
            data_types.add(data_type)

        _data_types = None
        if data_types:
            if self._data_types:
                raise Exception("'data_types' argument not allowed for this component.")
            _data_types = data_types
        else:
            _data_types = self._data_types
            if not _data_types:
                _data_types = [self.get_data_type()]

        _key = "_".join(sorted(_data_types))
        _key_selectbox = f"value_select_{key}_{_key}"

        if len(_data_types) == 1:
            dt = next(iter(_data_types))
            inp_comp = self.kiara.get_input_component(dt)
            if inp_comp and inp_comp.__class__ != self.__class__:
                return inp_comp.render_input_field(
                    st, _key_selectbox, label, *args, **kwargs
                )

        has_alias = kwargs.pop("has_alias", True)
        available_values = self.api.list_aliases(
            data_types=list(_data_types), has_alias=has_alias
        )

        with_preview = kwargs.get("preview", "auto")

        if with_preview == "auto":
            with_preview = "checkbox"

        if not with_preview or with_preview == "false":
            result = st.selectbox(
                label=label, options=available_values, key=_key_selectbox, **kwargs
            )
        else:
            result = st.selectbox(
                label=label, options=available_values, key=_key_selectbox, **kwargs
            )
            if with_preview == "checkbox":
                if result is None:
                    disabled = True
                else:
                    disabled = False
                show_preview = st.checkbox(
                    "Preview", key=f"preview_{_key_selectbox}", disabled=disabled
                )
                if show_preview:
                    if hasattr(st, "__enter__"):
                        with st:
                            self.kiara.preview(result)
                    else:
                        self.kiara.preview(result)
            elif with_preview:
                if result is not None:
                    if hasattr(st, "__enter__"):
                        with st:
                            self.kiara.preview(result)
                    else:
                        self.kiara.preview(result)

        return result


# class TableInput(InputComponent):
#
#     @classmethod
#     def get_data_type(cls) -> str:
#         return "table"
#
#     def _render_onboarding(self, st: DeltaGenerator, key: str, *args, **kwargs):
#         pass
#
#     def _render_preview(self, st: DeltaGenerator, key: str, value: Value):
#         pass
