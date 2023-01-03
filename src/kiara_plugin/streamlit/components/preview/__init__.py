# -*- coding: utf-8 -*-
import uuid
from abc import abstractmethod
from typing import Union

from kiara import Value
from kiara.registries.data import ValueLink
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class PreviewComponent:
    pass


class PreviewComponent(KiaraComponent):
    @classmethod
    @abstractmethod
    def get_data_type(cls) -> str:
        pass

    @classmethod
    def get_preview_name(cls) -> str:
        return "default"

    @abstractmethod
    def render_preview(self, st: DeltaGenerator, key: str, value: Value, **kwargs):
        pass

    def _render(
        self,
        st: DeltaGenerator,
        key: str,
        value: Union[str, uuid.UUID, ValueLink],
        **kwargs,
    ):

        self.render_preview(st=st, key=key, value=value, **kwargs)


class DefaultPreviewComponent(PreviewComponent):

    _component_name = "preview"

    @classmethod
    def get_data_type(cls) -> str:
        return "any"

    def render_preview(
        self,
        st: DeltaGenerator,
        key: str,
        value: Union[str, uuid.UUID, ValueLink],
        **kwargs,
    ):

        preview_name = kwargs.get("preview_name", None)
        height = kwargs.get("height", 400)

        _value = self.api.get_value(value)
        component = self._kiara_streamlit.get_preview_component(
            data_type=_value.data_type_name, preview_name=preview_name
        )
        if component is not None:
            component.render_func(st=st, key=key)(value=_value)
        else:
            if isinstance(value, Value):
                name = str(value.value_id)
            else:
                name = str(value)
            renderable = self.api.render_value(
                value=_value, target_format="string", use_pretty_print=True
            )
            st.text_area(
                f"Value: {name}", value=renderable, disabled=True, height=height
            )


class ValueList(KiaraComponent):

    _component_name = "value_list"

    def _render(self, st: DeltaGenerator, key: str, data_type: str = None):

        data_types = []
        if data_type:
            data_types.append(data_type)

        values = self.api.list_aliases(data_types=data_types)

        _key = f"{key}_list"
        selected_alias = create_list_component(
            st=st, key=_key, title="Values", items=list(values.keys())
        )

        return selected_alias


class ValueListPreview(KiaraComponent):

    _component_name = "value_list_preview"

    def _render(
        self,
        st: DeltaGenerator,
        key: str,
        data_type: str = None,
        ratio_preview: int = 3,
    ):

        data_list_column, preview_column = st.columns([1, ratio_preview])

        _key = f"{key}_data_list"
        with data_list_column:
            selected_alias = self.kiara.value_list(key=_key, data_type=data_type)

        if selected_alias:
            value = self.api.get_value(selected_alias)
            component = self.kiara.get_preview_component(value.data_type_name)

            if component is None:
                component = self.kiara.get_preview_component("any")

            component.render_preview(st=preview_column, key=key, value=value)

    def _render_preview(self, st: DeltaGenerator, key: str, value: Value):
        st.write(str(value))
