# -*- coding: utf-8 -*-
import atexit
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Mapping, Union

import streamlit as st
from kiara.api import KiaraAPI
from kiara.context import KiaraConfig, KiaraContextConfig, KiaraRuntimeConfig
from streamlit.runtime.scriptrunner import get_script_run_ctx

from kiara_plugin.streamlit.components import KiaraComponent
from kiara_plugin.streamlit.components.input import InputComponent
from kiara_plugin.streamlit.components.preview import PreviewComponent
from kiara_plugin.streamlit.defaults import kiara_stremalit_app_dirs
from kiara_plugin.streamlit.utils.class_loading import (
    find_all_kiara_streamlit_components,
)


class ComponentMgmt(object):
    def __init__(
        self,
        kiara_streamlit: "KiaraStreamlit",
        example_base_dir: Union[str, Path, None] = None,
    ):

        self._kiara_streamlit: KiaraStreamlit = kiara_streamlit
        self._exapmle_base_dir: Union[str, None, Path] = example_base_dir

        self._components: Union[Dict[str, KiaraComponent], None] = None
        self._preview_components: Union[
            Dict[str, Dict[str, PreviewComponent]], None
        ] = None
        self._input_components: Union[Dict[str, InputComponent], None] = None

    def add_component(self, name: str, component: KiaraComponent):

        if name in self.components:
            raise ValueError(f"Component with name '{name}' already exists.")

        self.components[name] = component  # type: ignore

    def get_component(self, name: str) -> Union[KiaraComponent, None]:
        return self.components.get(name, None)

    def get_preview_component(
        self, data_type: str, preview_name: Union[str, None] = None
    ) -> PreviewComponent:

        all_previews = self.preview_components.get(data_type, None)
        if not all_previews:
            raise Exception(f"No preview component found for data type: '{data_type}'")
        if preview_name and preview_name not in all_previews.keys():
            raise Exception(f"No preview component found for data type: '{data_type}'")

        if not preview_name:
            if len(all_previews) > 1:
                if "default" not in all_previews.keys():
                    raise ValueError(
                        f"Multiple previews available for data type '{data_type}', but no default preview defined."
                    )
                else:
                    preview_name = "default"
            else:
                preview_name = next(iter(all_previews.keys()))
        result = all_previews.get(preview_name, None)

        if not result:
            raise Exception(f"No preview component found for data type: '{data_type}'")
        else:
            return result

    def get_input_component(self, data_type: str) -> InputComponent:
        result = self.input_components.get(data_type, None)
        if result is None:
            raise Exception(f"No input component found for data type: '{data_type}'")
        return result

    @property
    def components(self) -> Mapping[str, KiaraComponent]:

        if self._components is not None:
            return self._components

        components = {}
        preview_components: Dict[str, Dict[str, PreviewComponent]] = {}
        input_components: Dict[str, InputComponent] = {}  # type: ignore

        base_input_cls = None
        for name, cls in find_all_kiara_streamlit_components().items():
            instance = cls(kiara_streamlit=self._kiara_streamlit, component_name=name)

            if name == "value_input":
                base_input_cls = cls

            components[name] = instance
            if issubclass(cls, PreviewComponent):
                data_type = cls.get_data_type()
                preview_name = cls.get_preview_name()
                if (
                    preview_components.get("data_type", {}).get("preview_name", None)
                    is not None
                ):
                    raise ValueError(
                        f"Can't register component for data type '{data_type}' and preview name '{preview_name}': more than one component registered."
                    )
                preview_components.setdefault(data_type, {})[preview_name] = instance  # type: ignore

            if issubclass(cls, InputComponent):
                data_type = cls.get_data_type()
                if data_type in input_components.keys():
                    raise Exception(
                        f"Multiple input components for data type: {data_type}"
                    )
                input_components[data_type] = instance  # type: ignore

        for data_type in self._kiara_streamlit.api.list_data_type_names():

            if self._kiara_streamlit.api.is_internal_data_type(data_type):
                continue

            if data_type not in input_components.keys():

                _doc = f"Render an input widget that prompts the user for a value of type '{data_type}'."
                _name = f"select_{data_type}"

                _example = {
                    "doc": f"Render an input widget for a value of type '{data_type}'.",
                    "args": {},
                }

                _comp = base_input_cls(kiara_streamlit=self._kiara_streamlit, component_name=_name, data_types=[data_type], doc=_doc)  # type: ignore
                _comp._instance_examples = [_example]  # type: ignore
                components[_name] = _comp
                input_components[data_type] = _comp  # type: ignore

        self._components = components
        self._preview_components = preview_components
        self._input_components = input_components
        return self._components

    @property
    def preview_components(self) -> Mapping[str, Mapping[str, PreviewComponent]]:
        if self._preview_components is None:
            self.components  # noqa
        return self._preview_components  # type: ignore

    @property
    def input_components(self) -> Mapping[str, InputComponent]:
        if self._input_components is None:
            self.components  # noqa
        return self._input_components  # type: ignore


class KiaraStreamlit(object):
    def __init__(
        self,
        context_config: Union[None, KiaraContextConfig] = None,
        runtime_config: Union[None, KiaraRuntimeConfig] = None,
    ):

        self._context_config: Union[None, KiaraContextConfig] = context_config
        self._runtime_config: Union[None, KiaraRuntimeConfig] = runtime_config

        self._api_outside_streamlit: Union[None, KiaraAPI] = None

        ctx = get_script_run_ctx()
        if ctx is None:
            # means, this is not running as streamlit script
            if self._api_outside_streamlit is None:
                kc = KiaraConfig()
                self._api_outside_streamlit = KiaraAPI(kc)
            self.api = self._api_outside_streamlit
        else:
            if "__kiara_api__" not in st.session_state.keys():
                kc = KiaraConfig()
                kiara_api = KiaraAPI(kc)
                st.session_state["__kiara_api__"] = kiara_api
            self.api = st.session_state.__kiara_api__

        self._component_mgmt = ComponentMgmt(
            kiara_streamlit=self, example_base_dir=None
        )

        self._temp_dir = os.path.join(
            kiara_stremalit_app_dirs.user_cache_dir, str(uuid.uuid4())
        )

        def del_temp_dir():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

        atexit.register(del_temp_dir)

        self.api  # noqa

        # self.add_component("test", TestComponent(kiara_streamlit=self))
        # self.add_component("help", HelpComponent(kiara_streamlit=self))

    def __getattr__(self, item):

        # if item in ["api", "components", "get_component"]:
        #     return getattr(self, item)
        if item == "api":
            import traceback

            traceback.print_stack()

        comp = self.get_component(item)
        if not comp:
            raise AttributeError(
                f"Kiara context object does not have component '{item}'."
            )

        return comp.render_func()

    # def add_component(self, name: str, component: KiaraComponent):
    #
    #     if name in self._avail_kiara_methods:
    #         raise ValueError(f"Can't add component with name '{name}', name is already used by Kiara context object.")
    #
    #     self._component_mgmt.add_component(name, component)

    # @property
    # def api(self) -> KiaraAPI:
    #
    #     ctx = get_script_run_ctx()
    #     if ctx is None:
    #         # means, this is not running as streamlit script
    #         if self._api_outside_streamlit is None:
    #             kc = KiaraConfig()
    #             self._api_outside_streamlit = KiaraAPI(kc)
    #         return self._api_outside_streamlit
    #     else:
    #         if "__kiara_api__" not in st.session_state.keys():
    #             kc = KiaraConfig()
    #             kiara_api = KiaraAPI(kc)
    #             st.session_state["__kiara_api__"] = kiara_api
    #         return st.session_state.__kiara_api__

    @property
    def components(self) -> Mapping[str, KiaraComponent]:
        return self._component_mgmt.components

    def get_preview_component(
        self, data_type: str, preview_name: Union[str, None] = None
    ) -> PreviewComponent:
        return self._component_mgmt.get_preview_component(
            data_type=data_type, preview_name=preview_name
        )

    def get_input_component(self, data_type: str) -> InputComponent:
        return self._component_mgmt.get_input_component(data_type=data_type)

    # def wants_onboarding(self) -> bool:
    #     onboarding = st.session_state.get(ONBOARD_MAKER_KEY, None)
    #     if onboarding and onboarding.get("enabled", False) is True:
    #         return True
    #     else:
    #         st.session_state.pop(ONBOARD_MAKER_KEY, None)
    #         return False

    def get_component(self, component_name: str) -> KiaraComponent:

        component = self._component_mgmt.get_component(component_name)
        if not component:
            raise Exception(f"No component availble for name: {component_name}")
        return component
