# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from streamlit_tags import st_tags

from kiara_plugin.streamlit.components.input import InputComponent, InputOptions

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ListInput(InputComponent):
    """Render a widget for input a list.

    Currently, only lists of strings are supported.
    """

    _component_name = "input_list"
    _examples = [
        {"doc": "A simple list input widget.", "args": {"label": "List of words"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "list"

    @classmethod
    def get_default_label(cls) -> str:
        return "Provide items"

    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: InputOptions,
    ):
        if options.smart_label:
            options.label = options.label.split("__")[-1]

        with st.container():
            items = st_tags(
                label=options.label,
                text="Press enter to add more",
                key=options.create_key("input", "list"),
            )
            if options.help:
                st.caption(options.help)

        value = self.api.register_data(items, data_type="list", reuse_existing=True)
        return value
