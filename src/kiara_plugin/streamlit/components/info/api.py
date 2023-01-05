# -*- coding: utf-8 -*-
import abc
from typing import List, Mapping, Union

from kiara import ValueSchema
from kiara.interfaces.python_api import (
    DataTypeClassesInfo,
    DataTypeClassInfo,
    ModuleTypeInfo,
    ModuleTypesInfo,
    OperationGroupInfo,
    OperationInfo,
)
from kiara.interfaces.python_api.models.info import InfoItemGroup, ItemInfo
from kiara.utils.output import create_dict_from_field_schemas
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class KiaraApiHelpCompOptions(ComponentOptions):
    pass


class KiaraApiHelpComponent(KiaraComponent[KiaraApiHelpCompOptions]):

    _component_name = "kiara_api_help"

    def _render(self, st: DeltaGenerator, options: KiaraApiHelpCompOptions):

        doc = self.api.doc
        left, right = st.columns([1, 3])

        _key = options.create_key("api_command_selection")
        method_names = sorted(doc.keys(), key=str.lower)
        selected_function = create_list_component(
            st=left, title="Functions", items=method_names, key=_key
        )

        if not selected_function:
            st.write("No function selected.")
        else:
            if selected_function in doc.keys():
                txt = doc[selected_function]
                with right:
                    st.text_area(
                        f"function: {selected_function}",
                        value=txt,
                        disabled=True,
                        height=360,
                        key=options.create_key("help_text"),
                    )


class InfoCompOptions(ComponentOptions):
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
            self.render_all_info(
                st=st,
                key=options.create_key("all_infos"),
                items=_items,
                options=options,
            )

        elif isinstance(items, str):

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
        else:
            raise NotImplementedError()

    @abc.abstractmethod
    def render_info(
        self, st: DeltaGenerator, key: str, item: ItemInfo, options: InfoCompOptions
    ):
        pass

    @abc.abstractmethod
    def render_all_info(
        self,
        st: DeltaGenerator,
        key: str,
        items: InfoItemGroup,
        options: InfoCompOptions,
    ):
        pass


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
        opts = FieldsInfoOptions(
            key=options.create_key("inputs"), fields=item.operation.inputs_schema
        )
        comp.render_func(st)(opts)

        st.markdown("##### Outputs")
        opts = FieldsInfoOptions(
            key=options.create_key("outputs"), fields=item.operation.outputs_schema
        )
        comp.render_func(st)(opts)

    def render_all_info(  # type: ignore
        self, st: DeltaGenerator, key: str, items: OperationGroupInfo, options: InfoCompOptions  # type: ignore
    ):

        left, right = st.columns([1, 3])
        selected_op = create_list_component(
            st=left,
            title="Operations",
            items=list(items.item_infos.keys()),
            key=f"{key}_operation_list",
        )

        if selected_op:
            op = items.item_infos[selected_op]
            self.render_info(
                st=right, key=f"{key}_{selected_op}", item=op, options=options
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

    def render_all_info(  # type: ignore
        self, st: DeltaGenerator, key: str, items: ModuleTypesInfo, options: InfoCompOptions  # type: ignore
    ):

        left, right = st.columns([1, 3])
        selected_module_type = create_list_component(
            st=left,
            title="Module types",
            items=list(items.item_infos.keys()),
            key=f"{key}_module_type_list",
        )

        if selected_module_type:
            op = items.item_infos[selected_module_type]
            self.render_info(
                st=right, key=f"{key}_{selected_module_type}", item=op, options=options
            )


class KiaraDataTypeInfoComponent(KiaraInfoComponent):

    _component_name = "data_type_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "data_type"

    def render_info(  # type: ignore
        self, st: DeltaGenerator, key: str, item: DataTypeClassInfo, options: InfoCompOptions  # type: ignore
    ):
        st.write(item)

    def render_all_info(  # type: ignore
        self, st: DeltaGenerator, key: str, items: DataTypeClassesInfo, options: InfoCompOptions  # type: ignore
    ):

        left, right = st.columns([1, 3])
        selected_data_type = create_list_component(
            st=left,
            title="Data types",
            items=list(items.item_infos.keys()),
            key=f"{key}_data_type_list",
        )

        if selected_data_type:
            op = items.item_infos[selected_data_type]
            self.render_info(
                st=right, key=f"{key}_{selected_data_type}", item=op, options=options
            )


class FieldsInfoOptions(ComponentOptions):

    fields: Mapping[str, ValueSchema] = Field(
        description="The fields and their schema."
    )


class FieldsInfo(KiaraComponent[FieldsInfoOptions]):

    _component_name = "fields_info"

    def _render(self, st: DeltaGenerator, options: FieldsInfoOptions):

        import pandas as pd

        fields = options.fields
        fields_data = create_dict_from_field_schemas(fields)
        df = pd.DataFrame(fields_data, columns=list(fields_data.keys()))
        df.set_index("field_name", inplace=True)
        st.table(df)
