# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Type

from kiara.api import Value, ValueMap
from kiara.models.documentation import DocumentationMetadataModel
from kiara_plugin.streamlit.components import ComponentInfo, ComponentsInfo
from kiara_plugin.streamlit.components.info import InfoCompOptions, KiaraInfoComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


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
        self, st: "KiaraStreamlitAPI", key: str, item: ComponentInfo, options: InfoCompOptions  # type: ignore
    ):
        st.markdown(f"#### Component: `{item.type_name}`")

        if item.examples:
            details_tab, examples_tab = st.tabs(["Details", "Examples"])
        else:
            tabs = st.tabs(["Details"])  # type: ignore
            # no idea, bug in streamlit?
            details_tab = tabs[0]

        with details_tab:
            details_tab.markdown(item.documentation.full_doc)

            expander = details_tab.expander("Component details", expanded=False)

            pkg_name = item.context.labels.get("package", "-- n/a --")
            table_md = f"""
            | attribute | value |
            | --------- | ----- |
            | Python class      | `{item.python_class.full_name}` |
            | Plugin            | `{pkg_name}` |
            """
            expander.markdown(table_md)
            expander.write("---")
            expander.write("##### Source code")
            expander.code(item.python_class.get_source_code())

            # comp = self.get_component("fields_info")
            details_tab.markdown("##### Arguments")
            arg_table: Dict[str, List[Any]] = {
                "field": [],
                "type": [],
                "required": [],
                "default": [],
                "description": [],
            }

            is_type_specific_select_comp = (
                item.python_class.full_name
                == "kiara_plugin.streamlit.components.input.DefaultInputComponent"
                and item.type_name != "select_value"
            )

            for arg_name in item.arguments.keys():

                # better hide this argument, otherwise it might be confusing
                if is_type_specific_select_comp and arg_name in [
                    "value_schema",
                    "data_type",
                ]:
                    continue

                arg = item.arguments[arg_name]
                arg_table["field"].append(arg_name)
                arg_table["type"].append(arg.python_type_string)
                arg_table["required"].append("yes" if arg.required else "no")
                arg_table["default"].append(
                    "" if arg.default is None else str(arg.default)
                )
                arg_table["description"].append(arg.description)

            hide_table_row_index = """
                        <style>
                        thead tr th:first-child {display:none}
                        tbody th {display:none}
                        </style>
                        """
            # Inject CSS with Markdown
            details_tab.markdown(hide_table_row_index, unsafe_allow_html=True)
            details_tab.table(arg_table)

            details_tab.markdown("##### Usage")
            code = """from kiara_plugin.streamlit import kiara_streamlit_init
st = kiara_streamlit_init

result = st.kiara.{}({})
            """.format(
                item.type_name, "<options>"
            )
            details_tab.code(code)

        if item.examples:
            with examples_tab:
                examples_tab.markdown("##### Examples")
                comp = self.get_component(item.type_name)
                for idx, example in enumerate(item.examples, start=1):
                    doc = example.get("doc", None)
                    if len(item.examples) > 1:
                        idx_str = f" #{idx}"
                    else:
                        idx_str = ""
                    if doc:
                        d = DocumentationMetadataModel.create(doc)
                        title = f"**Example{idx_str}**: *{d.description}*"
                        txt = d.doc
                    else:
                        title = f"**Example{idx_str}** *#{idx}*"
                        txt = None

                    with examples_tab.expander(title, expanded=idx == 1):

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

                        code = """from kiara_plugin.streamlit import kiara_streamlit_init
st = kiara_streamlit_init

result = st.kiara.{}({})
            """.format(
                            item.type_name, arg_str
                        )
                        self._st.code(code)

                        with self._st.expander(
                            "***Rendered component***", expanded=True
                        ):

                            try:
                                result = comp.render_func(self._st)(
                                    **example.get("args", {})
                                )
                            except Exception as e:
                                self._st.error(e)
                                result = None
                            if result:
                                title = "**Component result (not rendered)**"
                                if isinstance(result, Value):
                                    with self._st.expander(title):
                                        self._st.markdown(
                                            "Result type: [`Value`](https://dharpa.org/kiara/latest/reference/kiara/models/values/value/#kiara.models.values.value.Value)"
                                        )
                                        self.kiara_streamlit.preview(
                                            result, key=f"{key}_example_result_{idx}"
                                        )
                                elif isinstance(result, ValueMap):
                                    with self._st.expander(title):
                                        self._st.markdown(
                                            "Result type: [`ValueMap`](https://dharpa.org/kiara/latest/reference/kiara/models/values/value/#kiara.models.values.value.ValueMap)"
                                        )
                                        self.kiara_streamlit.value_map_preview(
                                            value_map=dict(result),
                                            key=f"{key}_example_result_map_{idx}",
                                        )
                                else:
                                    with self._st.expander(title):
                                        self._st.markdown(
                                            f"Result type: Python instace of type ``{type(result)}`'"
                                        )
                                        self._st.write(result)
