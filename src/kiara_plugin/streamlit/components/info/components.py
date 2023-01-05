# -*- coding: utf-8 -*-
from typing import Union

from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class HelpCompOptions(ComponentOptions):

    attribute: Union[str, None] = Field(description="The attribute to show help for.")


class HelpComponent(KiaraComponent[HelpCompOptions]):

    _component_name = "help"
    _options = HelpCompOptions

    def _render(self, st: DeltaGenerator, options: HelpCompOptions):

        attribute = options.attribute

        if not attribute:
            component_tab, api_tab = st.tabs(["components", "kiara_api"])

            with api_tab:
                self.kiara_streamlit.kiara_api_help()
            with component_tab:
                self.kiara_streamlit.kiara_component_help()

        elif attribute in self.api.doc.keys():
            st.markdown(self.api.doc[attribute])
        elif attribute in self.kiara_streamlit.components.keys():
            component = self.kiara_streamlit.components[attribute]
            try:
                _key = options.create_key("component_help", attribute)
                component.render_func(st)(key=_key)
            except Exception as e:
                st.error(e)
                import traceback

                traceback.print_exc()


class KiaraComponentHelpComponent(KiaraComponent):

    _component_name = "kiara_component_help"

    def _render(self, st: DeltaGenerator, options: ComponentOptions):

        components = self.kiara_streamlit.components

        left, right = st.columns([1, 3])
        items = sorted(
            (x for x in components.keys() if x not in ["kiara_component_help"]),
            key=str.lower,
        )

        _key = options.create_key("component", "help", "selection_list")
        selected_component = create_list_component(
            st=left, title="Components", items=items, key=_key
        )

        if selected_component in sorted(components.keys()):
            component = components[selected_component]
            with right:
                try:
                    _key = options.create_key("component", "help", selected_component)
                    component.render_func(st)(key=_key)
                except Exception as e:
                    st.error(e)
                    import traceback

                    traceback.print_exc()
