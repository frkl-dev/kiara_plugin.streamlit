# -*- coding: utf-8 -*-
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class HelpComponent(KiaraComponent):

    _component_name = "help"

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        attribute = kwargs.pop("attribute", None)
        if not attribute and args:
            attribute = args[0]

        if not attribute:
            component_tab, api_tab = st.tabs(["components", "kiara_api"])

            with api_tab:
                self.kiara.kiara_api_help()
            with component_tab:
                self.kiara.kiara_component_help()

        elif attribute in self.api.doc.keys():
            st.markdown(self.api.doc[attribute])
        elif attribute in self.kiara.components.keys():
            component = self.kiara.components[attribute]
            try:
                _key = f"component_help_{key}_{attribute}"
                component._render(st=st, key=_key)
            except Exception as e:
                st.error(e)
                import traceback

                traceback.print_exc()


class KiaraComponentHelpComponent(KiaraComponent):

    _component_name = "kiara_component_help"

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        components = self.kiara.components

        left, right = st.columns([1, 3])
        items = sorted(
            (x for x in components.keys() if x not in ["kiara_component_help"]),
            key=str.lower,
        )

        _key = f"component_help_{key}_selection_list"
        selected_component = create_list_component(
            st=left, title="Components", items=items, key=key
        )

        if selected_component in sorted(components.keys()):
            component = components[selected_component]
            with right:
                try:
                    _key = f"component_help_{key}_{selected_component}"
                    component._render(st=st, key=_key)
                except Exception as e:
                    st.error(e)
                    import traceback

                    traceback.print_exc()
