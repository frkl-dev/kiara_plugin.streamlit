# -*- coding: utf-8 -*-
import abc
import warnings
from functools import partial
from typing import Callable, Union

import streamlit as st

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
