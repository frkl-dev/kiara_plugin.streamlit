# -*- coding: utf-8 -*-
import uuid
from abc import abstractmethod
from typing import List, Mapping, Union

from kiara.api import Value, ValueMap
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class PreviewOptions(ComponentOptions):

    height: Union[int, None] = Field(
        description="The height of the preview.", default=None
    )
    display_style: str = Field(
        description="The display style to use for this preview.", default="default"
    )
    value: Union[str, uuid.UUID, Value] = Field(description="The value to preview.")


class PreviewComponent(KiaraComponent[PreviewOptions]):

    _options = PreviewOptions  # type: ignore

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
    """The default preview component, will render a preview component dependent on the data type of the provided value."""

    _component_name = "preview"
    _examples = [
        {"doc": "Preview a table value.", "args": {"value": "nodes_table"}},
    ]

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
            component.render_func(st)(value=_value, key=options.create_key("preview"))
        else:
            if isinstance(options.value, Value):
                name = str(_value.value_id)
            else:
                name = str(options.value)

            renderable = self.api.render_value(
                value=_value, target_format="string", use_pretty_print=True
            )
            st.text_area(
                f"Value: {name}",
                value=renderable,
                disabled=True,
                height=height,
                key=options.create_key("preview", "default"),
            )


class PreviewListOptions(ComponentOptions):

    data_types: Union[str, List[str], None] = Field(
        description="The data types to display.", default=None
    )


class ValueList(KiaraComponent[PreviewListOptions]):

    _component_name = "value_list"
    _options = PreviewListOptions

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


class ValueListPreview(KiaraComponent[PreviewListOptions]):

    _component_name = "value_list_preview"
    _options = PreviewListOptions

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
            component = self.kiara_streamlit.get_preview_component(value.data_type_name)

            if component is None:
                component = self.kiara_streamlit.get_preview_component("any")

            pr_opts = PreviewOptions(key=options.create_key("preview"), value=value)
            component.render_preview(preview_column, options=pr_opts)

        return selected_alias


class ValueMapPreviewOptions(ComponentOptions):

    add_value_types: bool = Field(
        description="Whether to add the type of the value to the tab titles.",
        default=True,
    )
    value_map: Mapping[str, Union[str, uuid.UUID, Value]] = Field(
        description="The values to display."
    )


class ValueMapPreview(KiaraComponent[ValueMapPreviewOptions]):

    _component_name = "value_map_preview"
    _options = ValueMapPreviewOptions

    def _render(
        self,
        st: DeltaGenerator,
        options: ValueMapPreviewOptions,
    ) -> Union[ValueMap, None]:

        if not options.value_map:
            st.write("-- no values --")
            return None

        _values = self.api.assemble_value_map(options.value_map)

        field_names = sorted(_values.keys())
        if not options.add_value_types:
            tab_names = field_names
        else:
            tab_names = sorted(
                (f"{x} ({_values[x].data_type_name})" for x in _values.keys())
            )

        tabs = st.tabs(tab_names)
        for idx, field in enumerate(field_names):

            value = _values[field]
            if not value.is_set:
                tabs[idx].markdown("-- value not set --")
            else:
                component = self.kiara_streamlit.get_preview_component(
                    value.data_type_name
                )
                if component is None:
                    component = self.kiara_streamlit.get_preview_component("any")
                center, right = tabs[idx].columns([4, 1])

                _key = options.create_key("preview", f"{idx}_{field}")
                preview_opts = PreviewOptions(key=_key, value=value)
                component.render_preview(st=center, options=preview_opts)

                right.write("Save value")
                with right.form(key=options.create_key("save_form", f"{idx}_{field}")):
                    _key = options.create_key("alias", f"{idx}_{field}")
                    alias = self._st.text_input(
                        "alias",
                        value="",
                        key=_key,
                        placeholder="alias",
                        label_visibility="hidden",
                    )
                    _key = options.create_key("save", f"{idx}_{field}")
                    save = self._st.form_submit_button("Save")

                if save and alias:
                    store_result = self.api.store_value(
                        value=value, alias=alias, allow_overwrite=False
                    )
                    if store_result.error:
                        right.error(store_result.error)
                    else:
                        right.success("Value saved")

        return _values
