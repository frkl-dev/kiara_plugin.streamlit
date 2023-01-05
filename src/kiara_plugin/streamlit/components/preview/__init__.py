# -*- coding: utf-8 -*-
import uuid
from abc import abstractmethod
from typing import List, Mapping, Union

from kiara import Value
from kiara.registries.data import ValueLink
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class PreviewOptions(ComponentOptions):

    value: Union[str, uuid.UUID, ValueLink] = Field(description="The value to preview.")
    height: Union[int, None] = Field(
        description="The height of the preview.", default=None
    )
    display_style: str = Field(
        description="The display style to use for this preview.", default="default"
    )


class PreviewComponent(KiaraComponent[PreviewOptions]):

    _options = PreviewOptions

    @classmethod
    @abstractmethod
    def get_data_type(cls) -> str:
        pass

    @classmethod
    def get_preview_name(cls) -> str:
        return "default"

    @abstractmethod
    def render_preview(self, st: DeltaGenerator, options: PreviewOptions):
        pass

    def _render(
        self,
        st: DeltaGenerator,
        options: PreviewOptions,
    ):

        self.render_preview(st=st, options=options)


class DefaultPreviewComponent(PreviewComponent):

    _component_name = "preview"

    @classmethod
    def get_data_type(cls) -> str:
        return "any"

    def render_preview(
        self,
        st: DeltaGenerator,
        options: PreviewOptions,
    ):

        preview_name = options.display_style
        height = options.height
        if not height:
            height = 400

        _value = self.api.get_value(options.value)
        if not _value.is_set:
            st.write("Value not set.")
            return

        component = self._kiara_streamlit.get_preview_component(
            data_type=_value.data_type_name, preview_name=preview_name
        )
        if component is not None:
            component.render_func()(value=_value)
        else:
            if isinstance(options.value, Value):
                name = str(_value.value_id)
            else:
                name = str(options.value)

            renderable = self.api.render_value(
                value=_value, target_format="string", use_pretty_print=True
            )
            st.text_area(
                f"Value: {name}", value=renderable, disabled=True, height=height
            )


class PreviewListOptions(ComponentOptions):

    data_types: Union[str, List[str], None] = Field(
        description="The data types to display.", default=None
    )


class ValueList(KiaraComponent):

    _component_name = "value_list"

    def _render(
        self, st: DeltaGenerator, options: PreviewListOptions
    ) -> Union[str, None]:

        data_types = []
        if options.data_types:
            if isinstance(options.data_types, str):
                data_types.append(options.data_types)
            else:
                data_types.extend(options.data_types)

        values = self.api.list_aliases(data_types=data_types)

        _key = options.create_key("value_list")
        selected_alias = create_list_component(
            st=st, key=_key, title="Values", items=list(values.keys())
        )

        return selected_alias


class ValueListPreview(KiaraComponent):

    _component_name = "value_list_preview"

    def _render(
        self,
        st: DeltaGenerator,
        options: PreviewListOptions,
    ) -> Union[str, None]:
        ratio_preview: int = 3
        data_list_column, preview_column = st.columns([1, ratio_preview])

        _key = options.create_key("data_list")

        comp = self.get_component("value_list")
        selected_alias = comp.render_func(data_list_column)(
            key=_key, data_types=options.data_types
        )

        if selected_alias:
            value = self.api.get_value(selected_alias)
            component = self.kiara.get_preview_component(value.data_type_name)

            if component is None:
                component = self.kiara.get_preview_component("any")

            pr_opts = PreviewOptions(key=options.create_key("preview"), value=value)
            component.render_preview(preview_column, options=pr_opts)

        return selected_alias


class ValuesPreviewOptions(ComponentOptions):
    values: Mapping[str, Value] = Field(description="The values to display.")


class ValuesPreview(KiaraComponent):

    _component_name = "values_preview"

    def _render(
        self,
        st: DeltaGenerator,
        options: ValuesPreviewOptions,
    ) -> Union[Value, None]:

        if not options.values:
            st.write("-- no values --")
            return None

        field_names = sorted(options.values.keys())
        tabs = st.tabs(field_names)
        selected = None
        for idx, field in enumerate(field_names):

            value = options.values[field]
            component = self.kiara.get_preview_component(value.data_type_name)
            if component is None:
                component = self.kiara.get_preview_component("any")
            left, center, right = tabs[idx].columns([1, 4, 1])

            _key = options.create_key("select", f"{idx}_{field}")
            select = left.button("Select for next step", key=_key)
            _key = options.create_key("preview", f"{idx}_{field}")
            preview_opts = PreviewOptions(key=_key, value=value)
            component.render_preview(st=center, options=preview_opts)
            right.write("")
            right.write("")
            right.write("")
            right.write("")
            right.write("")
            right.write("Save value")
            _key = options.create_key("alias", f"{idx}_{field}")
            alias = right.text_input("alias", value="", key=_key)
            _key = options.create_key("save", f"{idx}_{field}")
            save = right.button("Save", disabled=not alias, key=_key)

            if save and alias:
                store_result = self.api.store_value(value=value, aliases=alias)
                if store_result.error:
                    right.error(store_result.error)
                else:
                    right.success("Value saved")
            if select:
                selected = field

        if selected:
            return options.values[selected]
        else:
            return None
