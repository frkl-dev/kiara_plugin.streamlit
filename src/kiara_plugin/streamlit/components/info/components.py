# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Mapping, Type

from kiara.api import Value, ValueMap
from kiara.models.documentation import DocumentationMetadataModel
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentInfo, ComponentsInfo
from kiara_plugin.streamlit.components.info import InfoCompOptions, KiaraInfoComponent


class KiaraComponentInfoComponent(KiaraInfoComponent[ComponentInfo]):
    """Display information about a kiara streamlit component.

    This is used to create what you see here.
    """

    _component_name = "component_info"

    _examples = [
        {
            "doc": "Display component info for the 'input_boolean' component.",
            "args": {"items": "input_boolean"},
        },
    ]

    @classmethod
    def get_info_type(cls) -> Type[ComponentInfo]:
        return ComponentInfo

    def get_all_item_infos(self) -> Mapping[str, ComponentInfo]:

        components = self.kiara_streamlit.components

        infos = ComponentsInfo.create_from_instances(
            title="All components",
            kiara=self.kiara_streamlit.api.context,
            instances=components,
        )

        # filter out workflow components, those are not ready yet
        items = {}
        for name, info in infos.item_infos.items():
            if "workflows" in info.context.tags:
                continue
            else:
                items[name] = info

        return items

    def get_info_item(self, item_id: str) -> ComponentInfo:

        comp = self.kiara_streamlit.get_component(item_id)
        return ComponentInfo.create_from_instance(
            kiara=self.kiara_streamlit.api.context, instance=comp
        )

    def render_info(  # type: ignore
        self, st: DeltaGenerator, key: str, item: ComponentInfo, options: InfoCompOptions  # type: ignore
    ):
        st.markdown(f"#### Component: `{item.type_name}`")
        st.markdown(item.documentation.full_doc)

        comp = self.get_component("fields_info")
        st.markdown("##### Arguments")
        arg_table: Dict[str, List[Any]] = {
            "field": [],
            "type": [],
            "required": [],
            "default": [],
            "description": [],
        }
        for arg_name in item.arguments.keys():
            arg = item.arguments[arg_name]
            arg_table["field"].append(arg_name)
            arg_table["type"].append(arg.python_type)
            arg_table["required"].append("yes" if arg.required else "no")
            arg_table["default"].append("" if arg.default is None else str(arg.default))
            arg_table["description"].append(arg.description)

        st.table(arg_table)

        st.markdown("##### Usage")
        code = """import streamlit as st
import kiara_plugin.streamlit as kst
kst.init()

result = st.kiara.{}({})
        """.format(
            item.type_name, "<options>"
        )
        st.code(code)

        if item.examples:
            st.markdown("##### Examples")
            comp = self.get_component(item.type_name)
            for idx, example in enumerate(item.examples, start=1):
                doc = example.get("doc", None)
                if doc:
                    d = DocumentationMetadataModel.create(doc)
                    title = f"**Example**: *{d.description}*"
                    txt = d.doc
                else:
                    title = f"**Example** *#{idx}*"
                    txt = None

                with st.expander(title, expanded=idx == 1):

                    if txt:
                        self._st.markdown(txt)

                    _options = []
                    example_args = example.get("args", {})
                    for arg_name in item.arguments.keys():
                        if arg_name in example_args.keys():
                            v = example_args[arg_name]
                            if isinstance(v, str):
                                v = f'"{v}"'
                            else:
                                v = str(v)
                            _options.append(f"{arg_name}={v}")

                    arg_str = ", ".join(_options)

                    code = """result = st.kiara.{}({})
        """.format(
                        item.type_name, arg_str
                    )
                    self._st.code(code)

                    with self._st.expander("***Rendered component***", expanded=True):

                        try:
                            result = comp.render_func(self._st)(
                                **example.get("args", {})
                            )
                        except Exception as e:
                            st.error(e)
                            result = None
                        if result:
                            if isinstance(result, Value):
                                with self._st.expander("*result*"):
                                    self.kiara_streamlit.preview(result)
                            elif isinstance(result, ValueMap):
                                with self._st.expander("*result*"):
                                    self.kiara_streamlit.value_map_preview(
                                        value_map=dict(result)
                                    )
                            else:
                                with self._st.expander("*result*"):
                                    self._st.markdown(f"***Result***: {result}")
