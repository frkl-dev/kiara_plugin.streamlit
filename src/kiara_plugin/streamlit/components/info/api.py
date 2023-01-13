# -*- coding: utf-8 -*-
import abc
from typing import List, Mapping, Tuple, Union

from kiara import ValueSchema
from kiara.interfaces.python_api import DataTypeClassInfo, ModuleTypeInfo, OperationInfo
from kiara.interfaces.python_api.models.info import InfoItemGroup, ItemInfo
from kiara.utils.output import create_dict_from_field_schemas
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class KiaraApiHelpCompOptions(ComponentOptions):
    class Config:
        arbitrary_types_allowed = True

    columns: Union[Tuple[int, int], Tuple[DeltaGenerator, DeltaGenerator]] = Field(
        description="The column layout to use for the next step.", default=(1, 4)
    )
    height: Union[int, None] = Field(
        description="The height of the list component.", default=None
    )


class KiaraApiHelpComponent(KiaraComponent[KiaraApiHelpCompOptions]):

    _component_name = "kiara_api_help"

    def _render(self, st: DeltaGenerator, options: KiaraApiHelpCompOptions):

        doc = self.api.doc
        left, right = options.columns
        if isinstance(left, int):
            left, right = st.columns(options.columns)

        _key = options.create_key("api_command_selection")
        method_names = sorted(doc.keys(), key=str.lower)
        selected_function = create_list_component(
            st=left,
            title="Functions",
            items=method_names,
            key=_key,
            height=options.height,
        )

        if not selected_function:
            st.write("No function selected.")
        else:
            if selected_function in doc.keys():
                txt = doc[selected_function]
                with right:  # type: ignore
                    st.text_area(
                        f"function: {selected_function}",
                        value=txt,
                        disabled=True,
                        height=options.height,
                        key=options.create_key("help_text"),
                    )


class InfoCompOptions(ComponentOptions):
    class Config:
        arbitrary_types_allowed = True

    columns: Union[
        Tuple[int, int], Tuple[DeltaGenerator, DeltaGenerator], None
    ] = Field(description="The column layout to use for the next step.", default=(1, 4))
    height: Union[int, None] = Field(
        description="The height of the list component.", default=None
    )
    items: Union[str, List[str], None] = Field(
        description="The item(s) to show info for."
    )


class KiaraInfoComponent(KiaraComponent[InfoCompOptions]):

    _options = InfoCompOptions

    @classmethod
    @abc.abstractmethod
    def get_info_type(cls) -> str:
        pass

    def _render(self, st: DeltaGenerator, options: InfoCompOptions):

        items = options.items
        if items is None:
            method = f"get_{self.get_info_type()}s_info"
            if not hasattr(self.api, method):
                method = f"retrieve_{self.get_info_type()}s_info"
                if not hasattr(self.api, method):
                    raise Exception(f"No method '{method}' found on kiara api object.")

            _items = getattr(self.api, method)()
            selected = self.render_all_info(
                st=st,
                key=options.create_key("all_infos"),
                items=_items,
                options=options,
            )
            return selected

        elif isinstance(items, str):

            # ignoring columns
            method = f"get_{self.get_info_type()}_info"
            if not hasattr(self.api, method):
                method = f"retrieve_{self.get_info_type()}_info"
                if not hasattr(self.api, method):
                    raise Exception(f"No method '{method}' found on kiara api object.")

            _item = getattr(self.api, method)(items)

            self.render_info(
                st=st,
                key=options.create_key(f"info_{items}"),
                item=_item,
                options=options,
            )
            return items
        else:
            raise NotImplementedError()

    @abc.abstractmethod
    def render_info(
        self, st: DeltaGenerator, key: str, item: ItemInfo, options: InfoCompOptions
    ):
        pass

    def render_all_info(  # type: ignore
        self,
        st: DeltaGenerator,
        key: str,
        items: InfoItemGroup,
        options: InfoCompOptions,
    ) -> Union[None, str]:

        if options.columns is None:
            left, right = st.columns((1, 4))
        elif isinstance(options.columns[0], int):
            left, right = st.columns(options.columns)
        else:
            left, right = options.columns

        selected_op = create_list_component(
            st=left,
            title=self.__class__.get_info_type().capitalize(),
            items=list(items.item_infos.keys()),
            key=f"{key}_{self.__class__.get_info_type()}_list",
            height=options.height,
        )

        if selected_op:
            op = items.item_infos[selected_op]
            self.render_info(
                st=right,
                key=f"{key}__{self.__class__.get_info_type()}_{selected_op}",
                item=op,
                options=options,
            )

        return selected_op


class KiaraOperationInfoComponent(KiaraInfoComponent):

    _component_name = "operation_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "operation"

    def render_info(  # type: ignore
        self, st: DeltaGenerator, key: str, item: OperationInfo, options: InfoCompOptions  # type: ignore
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


class KiaraModuleTypeInfoComponent(KiaraInfoComponent):

    _component_name = "module_type_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "module_type"

    def render_info(  # type: ignore
        self, st: DeltaGenerator, key: str, item: ModuleTypeInfo, options: InfoCompOptions  # type: ignore
    ):
        st.write(item)


class KiaraDataTypeInfoComponent(KiaraInfoComponent):

    _component_name = "data_type_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "data_type"

    def render_info(  # type: ignore
        self, st: DeltaGenerator, key: str, item: DataTypeClassInfo, options: InfoCompOptions  # type: ignore
    ):
        st.write(item)


class FieldsInfoOptions(ComponentOptions):

    fields: Mapping[str, ValueSchema] = Field(
        description="The fields and their schema."
    )


class FieldsInfo(KiaraComponent[FieldsInfoOptions]):

    _component_name = "fields_info"
    _options = FieldsInfoOptions

    def _render(self, st: DeltaGenerator, options: FieldsInfoOptions):

        import pandas as pd

        fields = options.fields
        fields_data = create_dict_from_field_schemas(fields)
        df = pd.DataFrame(fields_data, columns=list(fields_data.keys()))
        df.set_index("field_name", inplace=True)
        st.table(df)


class OperationDocsOptions(ComponentOptions):
    pass


class OperationDocs(KiaraComponent):

    _component_name = "operation_documentation"
    _options = OperationDocsOptions

    def _render(self, st: DeltaGenerator, options: OperationDocsOptions):

        left, right = st.columns([1, 3])

        tab_names = ["Overview", "Demo"]
        overview, demo = right.tabs(tab_names)

        op_info = self.get_component("operation_info")
        selected = op_info.render_func(st)(
            key="op_info", columns=(left, overview), height=500
        )

        if not selected:
            demo.markdown("No operation selected.")
        else:
            code = """import streamlit as st
import kiara_plugin.streamlit as kst
kst.init()

result = st.kiara.process_operation("{}")
""".format(
                selected
            )

            demo.code(code)
            comp = self.get_component("process_operation")
            comp.render_func(demo)(
                key=options.create_key("demo"), operation_id=selected
            )
