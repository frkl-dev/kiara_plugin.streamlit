# -*- coding: utf-8 -*-
import abc
import warnings
from functools import partial
from typing import Any, Callable, Generic, List, Type, TypeVar, Union

import streamlit as st
from pydantic import BaseModel, Field

with warnings.catch_warnings():
    pass

from typing import TYPE_CHECKING

from streamlit.delta_generator import DeltaGenerator

if TYPE_CHECKING:
    from kiara import KiaraAPI

    from kiara_plugin.streamlit import KiaraStreamlit


class ComponentOptions(BaseModel):

    key: str = Field(description="The (base) key to use for this component.")

    def create_key(self, *args) -> str:

        base = ["kiara", self.key]
        base.extend(args)
        _key = "__".join(base)
        return _key

    def get_session_key(self, *key: str) -> str:

        if not key:
            raise Exception("No key provided.")
        _key = [self.create_key(*key[0:-1]), "session_value", key[-1]]
        return "__".join(_key)


COMP_OPTIONS_TYPE = TypeVar("COMP_OPTIONS_TYPE", bound=ComponentOptions)


class KiaraComponent(abc.ABC, Generic[COMP_OPTIONS_TYPE]):

    _options: Type[COMP_OPTIONS_TYPE] = ComponentOptions  # type: ignore

    def __init__(self, kiara_streamlit: "KiaraStreamlit"):
        self._kiara_streamlit: KiaraStreamlit = kiara_streamlit
        self._st: DeltaGenerator = st  # type: ignore

    @property
    def api(self) -> "KiaraAPI":
        return self._kiara_streamlit.api

    @property
    def kiara_streamlit(self) -> "KiaraStreamlit":
        return self._kiara_streamlit

    def default_key(self) -> str:
        return f"Component:{self.__class__.__name__}"

    def get_session_var(
        self, options: "ComponentOptions", *key: str, default: Any = None
    ) -> Any:

        session_key = options.get_session_key(*key)

        if session_key not in self._st.session_state:
            return default

        value = self._st.session_state[session_key]
        return value

    def set_session_var(
        self, options: "ComponentOptions", *key: str, value: Any
    ) -> None:

        session_key = options.get_session_key(*key)
        self._st.session_state[session_key] = value

    def render_func(self, st: Union[DeltaGenerator, None] = None) -> Callable:

        if st is None:
            st = self._st

        return partial(self.render, st)

    def get_option_names(self) -> List[str]:

        option_fields = list(self.__class__._options.__fields__.keys())
        option_fields.reverse()
        return option_fields

    def render(self, st: DeltaGenerator, *args, **kwargs) -> Any:

        option_fields = self.get_option_names()

        for idx, arg in enumerate(args):
            try:
                key = option_fields[idx]
            except Exception:
                raise Exception(
                    f"Invalid number of positional arguments for component '{self.__class__.__name__}'."
                )

            if key in kwargs.keys():
                raise Exception(f"Duplicate value for key '{key}'.")

            if key == "key":
                continue
            kwargs[key] = arg

        if "key" not in kwargs.keys():
            kwargs["key"] = self.default_key()

        options = self.__class__._options(**kwargs)

        return self._render(st, options)

    @abc.abstractmethod
    def _render(self, st: DeltaGenerator, options: COMP_OPTIONS_TYPE):
        pass

    def get_component(self, component_name: str) -> "KiaraComponent":
        result = self._kiara_streamlit.get_component(component_name)
        return result
