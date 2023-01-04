# -*- coding: utf-8 -*-
import abc

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
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class KiaraApiHelpComponent(KiaraComponent):

    _component_name = "kiara_api_help"

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        doc = self.api.doc
        left, right = st.columns([1, 3])

        _key = f"{key}_api_command_selection"
        method_names = sorted(doc.keys(), key=str.lower)
        selected_function = create_list_component(
            st=left, title="Functions", items=method_names, key=_key
        )

        if selected_function in doc.keys():
            txt = doc[selected_function]
            with right:
                st.text_area(
                    f"function: {selected_function}",
                    value=txt,
                    disabled=True,
                    height=360,
                    key=f"{key}_doc",
                )


class KiaraInfoComponent(KiaraComponent):
    @classmethod
    @abc.abstractmethod
    def get_info_type(cls) -> str:
        pass

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        item = kwargs.pop("item", None)

        if item and args:
            raise Exception(
                f"Can't use 'item' and positional arguments at the same time."
            )
        elif not item and args:
            if len(args) != 1:
                raise Exception(
                    "Multiple positional arguments not allowed, only use one to signify the item to show or none and use the 'item' keyword argument."
                )
            item = args[0]
            args = []

        if item:

            method = f"get_{self.get_info_type()}_info"
            if not hasattr(self.api, method):
                method = f"retrieve_{self.get_info_type()}_info"
                if not hasattr(self.api, method):
                    raise Exception(f"No method '{method}' found on kiara api object.")

            _item = getattr(self.api, method)(item)

            self.render_info(st=st, key=key, item=_item, *args, **kwargs)
        else:
            items = kwargs.pop("items", None)
            if not items:
                method = f"get_{self.get_info_type()}s_info"
                if not hasattr(self.api, method):
                    method = f"retrieve_{self.get_info_type()}s_info"
                    if not hasattr(self.api, method):
                        raise Exception(
                            f"No method '{method}' found on kiara api object."
                        )

                print(f"METHOD: {method}")
                _items = getattr(self.api, method)(item)
            else:
                raise NotImplementedError()
            self.render_all_info(st=st, key=key, items=_items, *args, **kwargs)

    @abc.abstractmethod
    def render_info(
        self, st: DeltaGenerator, key: str, item: ItemInfo, *args, **kwargs
    ):
        pass

    @abc.abstractmethod
    def render_all_info(
        self, st: DeltaGenerator, key: str, items: InfoItemGroup, *args, **kwargs
    ):
        pass


class KiaraOperationInfoComponent(KiaraInfoComponent):

    _component_name = "operation_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "operation"

    def render_info(
        self, st: DeltaGenerator, key: str, item: OperationInfo, *args, **kwargs
    ):
        st.markdown(f"#### Operation: `{item.operation.operation_id}`")
        st.markdown(item.documentation.full_doc)

        comp = st.kiara.get_component("fields_info")
        st.markdown(f"##### Inputs")
        comp.render_func(st, f"{key}_inputs")(item.operation.inputs_schema)

        st.markdown(f"##### Outputs")
        comp.render_func(st, f"{key}_inputs")(item.operation.outputs_schema)

    def render_all_info(
        self, st: DeltaGenerator, key: str, items: OperationGroupInfo, *args, **kwargs
    ):

        left, right = st.columns([1, 3])
        selected_op = create_list_component(
            st=left,
            title="Operations",
            items=list(items.item_infos.keys()),
            key=f"{key}_operation_list",
        )

        if selected_op:
            op = items.item_infos.get(selected_op, None)
            self.render_info(
                st=right, key=f"{key}_{selected_op}", item=op, *args, **kwargs
            )


class KiaraModuleTypeInfoComponent(KiaraInfoComponent):

    _component_name = "module_type_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "module_type"

    def render_info(
        self, st: DeltaGenerator, key: str, item: ModuleTypeInfo, *args, **kwargs
    ):
        st.write(item)

    def render_all_info(
        self, st: DeltaGenerator, key: str, items: ModuleTypesInfo, *args, **kwargs
    ):

        left, right = st.columns([1, 3])
        selected_module_type = create_list_component(
            st=left,
            title="Module types",
            items=list(items.item_infos.keys()),
            key=f"{key}_module_type_list",
        )

        if selected_module_type:
            op = items.item_infos.get(selected_module_type, None)
            self.render_info(
                st=right, key=f"{key}_{selected_module_type}", item=op, *args, **kwargs
            )


class KiaraDataTypeInfoComponent(KiaraInfoComponent):

    _component_name = "data_type_info"

    @classmethod
    def get_info_type(cls) -> str:
        return "data_type"

    def render_info(
        self, st: DeltaGenerator, key: str, item: DataTypeClassInfo, *args, **kwargs
    ):
        st.write(item)

    def render_all_info(
        self, st: DeltaGenerator, key: str, items: DataTypeClassesInfo, *args, **kwargs
    ):

        left, right = st.columns([1, 3])
        selected_data_type = create_list_component(
            st=left,
            title="Data types",
            items=list(items.item_infos.keys()),
            key=f"{key}_data_type_list",
        )

        if selected_data_type:
            op = items.item_infos.get(selected_data_type, None)
            self.render_info(
                st=right, key=f"{key}_{selected_data_type}", item=op, *args, **kwargs
            )


class FieldsInfo(KiaraComponent):

    _component_name = "fields_info"

    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):

        import pandas as pd

        fields = kwargs.pop("fields", None)
        if fields is None and args:
            fields = args[0]

        fields_data = create_dict_from_field_schemas(fields)
        df = pd.DataFrame(fields_data, columns=list(fields_data.keys()))
        df.set_index("field_name", inplace=True)
        st.table(df)
