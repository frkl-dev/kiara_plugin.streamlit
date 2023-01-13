# -*- coding: utf-8 -*-
from streamlit.delta_generator import DeltaGenerator
from streamlit_tags import st_tags

from kiara_plugin.streamlit.components.input import InputComponent, InputOptions


class ListInput(InputComponent):

    _component_name = "input_list"

    @classmethod
    def get_data_type(cls) -> str:
        return "list"

    @classmethod
    def get_default_label(cls) -> str:
        return "Provide items"

    def render_input_field(
        self,
        st: DeltaGenerator,
        options: InputOptions,
    ):
        if options.smart_label:
            options.label = options.label.split("__")[-1]

        # current = self.get_session_var(options, "input", "list", default=[])
        with st:
            items = st_tags(
                label="Enter items",
                text="Press enter to add more",
                key=options.create_key("input", "list"),
            )

        value = self.api.register_data(items, data_type="list", reuse_existing=True)
        return value
