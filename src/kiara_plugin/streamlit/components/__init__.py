# -*- coding: utf-8 -*-
import abc
import warnings
from functools import partial
from typing import Callable, Union

import streamlit as st
from kiara.interfaces.python_api.models.info import (
    DataTypeClassesInfo,
    DataTypeClassInfo,
    InfoItemGroup,
    ItemInfo,
    ModuleTypeInfo,
    ModuleTypesInfo,
    OperationGroupInfo,
    OperationInfo,
)

from kiara_plugin.streamlit.utils.components import create_list_component

with warnings.catch_warnings():
    pass

from typing import TYPE_CHECKING

from streamlit.delta_generator import DeltaGenerator

if TYPE_CHECKING:
    from kiara import KiaraAPI

    from kiara_plugin.streamlit import KiaraStreamlit


class KiaraComponent(abc.ABC):
    def __init__(self, kiara_streamlit: "KiaraStreamlit"):
        self._kiara_streamlit: KiaraStreamlit = kiara_streamlit
        self._st = st

    @property
    def api(self) -> "KiaraAPI":
        return self._kiara_streamlit.api

    @property
    def kiara(self) -> "KiaraStreamlit":
        return self._kiara_streamlit

    @property
    def default_key(self) -> str:
        return f"key_{self.__class__.__name__}"

    def render_func(
        self, st: Union[DeltaGenerator, None] = None, key: Union[str, None] = None
    ) -> Callable:

        if st == None:
            st = self._st
        if not key:
            key = self.default_key
        return partial(self._render, st, key)

    @abc.abstractmethod
    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):
        pass

    def get_component(self, component_name: str) -> Union["KiaraComponent", None]:
        return self._kiara_streamlit.get_component(component_name)


class TestComponent(KiaraComponent):
    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):
        st.write("Hello world")


class Test2Component(KiaraComponent):
    def _render(self, st: DeltaGenerator, key: str, *args, **kwargs):
        st.write("Hello world")


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
        st.write(item)

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
