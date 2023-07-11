# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, ClassVar, Mapping, Type, Union

from pydantic import Field

from kiara.interfaces.python_api import OperationInfo
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.info import InfoCompOptions, KiaraInfoComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI

# class KiaraApiHelpCompOptions(ComponentOptions):
#     class Config:
#         arbitrary_types_allowed = True
#
#     columns: Union[Tuple[int, int], Tuple[DeltaGenerator, DeltaGenerator]] = Field(
#         description="The column layout to use for the next step.", default=(1, 4)
#     )
#     height: Union[int, None] = Field(
#         description="The height of the list component.", default=None
#     )
#
#
# class KiaraApiHelpComponent(KiaraComponent[KiaraApiHelpCompOptions]):
#
#     _component_name = "kiara_api_help"
#
#     def _render(self, st: KiaraStreamlitAPI, options: KiaraApiHelpCompOptions):
#
#         doc = self.api.doc
#         left, right = options.columns
#         if isinstance(left, int):
#             left, right = st.columns(options.columns)  # type: ignore
#
#         _key = options.create_key("api_command_selection")
#         method_names = sorted(doc.keys(), key=str.lower)
#         selected_function = create_list_component(
#             st=left,
#             title="Functions",
#             items=method_names,
#             key=_key,
#             height=options.height,
#         )
#
#         if not selected_function:
#             st.write("No function selected.")
#         else:
#             if selected_function in doc.keys():
#                 txt = doc[selected_function]
#                 with right:  # type: ignore
#                     st.text_area(
#                         f"function: {selected_function}",
#                         value=txt,
#                         disabled=True,
#                         height=options.height,
#                         key=options.create_key("help_text"),
#                     )


class KiaraOperationInfoComponent(KiaraInfoComponent[OperationInfo]):
    """Displays information for all or a single operation.

    If you only provide a single item, documentation for this item will be shown. Otherwise, a list
    will be rendered on the left, and users can select one of the available items to get information for.
    """

    _component_name = "operation_info"
    _examples: ClassVar = [
        {
            "doc": "Show information for the 'create.table.from.file' operation.",
            "args": {"items": "create.table.from.file"},
        },
        {"doc": "Show informations for all available operations.", "args": {}},
    ]

    @classmethod
    def get_info_type(cls) -> Type[OperationInfo]:
        return OperationInfo

    def get_all_item_infos(self) -> Mapping[str, OperationInfo]:

        return self.api.retrieve_operations_info().item_infos

    def get_info_item(self, item_id: str) -> OperationInfo:

        return self.api.retrieve_operation_info(operation=item_id)

    def render_info(  # type: ignore
        self, st: "KiaraStreamlitAPI", key: str, item: OperationInfo, options: InfoCompOptions  # type: ignore
    ):
        st.markdown(f"#### Operation: `{item.operation.operation_id}`")
        st.markdown(item.documentation.full_doc)

        comp = self.get_component("fields_info")
        st.markdown("##### Inputs")
        # opts = FieldsInfoOptions(
        #     key=options.create_key("inputs"), fields=item.operation.inputs_schema
        # )
        comp.render_func(st)(
            key=options.create_key("inputs"), fields=item.operation.inputs_schema
        )

        st.markdown("##### Outputs")
        # opts = FieldsInfoOptions(
        #     key=options.create_key("outputs"), fields=item.operation.outputs_schema
        # )
        comp.render_func(st)(
            key=options.create_key("outputs"), fields=item.operation.outputs_schema
        )


# class KiaraModuleTypeInfoComponent(KiaraInfoComponent):
#
#     _component_name = "module_type_info"
#
#     @classmethod
#     def get_info_type(cls) -> str:
#         return "module_type"
#
#     def render_info(  # type: ignore
#         self, st: KiaraStreamlitAPI, key: str, item: ModuleTypeInfo, options: InfoCompOptions  # type: ignore
#     ):
#         st.write(item)
#
#
# class KiaraDataTypeInfoComponent(KiaraInfoComponent):
#
#     _component_name = "data_type_info"
#
#     @classmethod
#     def get_info_type(cls) -> str:
#         return "data_type"
#
#     def render_info(  # type: ignore
#         self, st: KiaraStreamlitAPI, key: str, item: DataTypeClassInfo, options: InfoCompOptions  # type: ignore
#     ):
#         st.write(item)


class OperationDocsOptions(ComponentOptions):
    height: Union[int, None] = Field(
        description="The height of the list component.", default=400
    )


class OperationDocs(KiaraComponent):
    """Displays documentation for all available operations."""

    _component_name = "operation_documentation"
    _options = OperationDocsOptions

    _examples: ClassVar = [
        {
            "doc": "Display operations doc.",
        },
    ]

    def _render(self, st: "KiaraStreamlitAPI", options: OperationDocsOptions):

        left, right = st.columns([1, 3])

        tab_names = ["Overview", "Demo"]
        overview, demo = right.tabs(tab_names)

        op_info = self.get_component("operation_info")
        selected: Union[OperationInfo, None] = op_info.render_func(st)(
            key=options.create_key("ops_info"),
            columns=(left, overview),
            height=options.height,
        )

        if not selected:
            demo.markdown("No operation selected.")
        else:
            code = """import streamlit as st
import kiara_plugin.streamlit as kst
kst.init()

result = st.kiara.process_operation("{}")
""".format(
                selected.operation.operation_id
            )

            demo.code(code)
            comp = self.get_component("operation_process_panel")
            comp.render_func(demo)(
                key=options.create_key("demo"),
                operation_id=selected.operation.operation_id,
            )
