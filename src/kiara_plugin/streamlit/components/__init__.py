# -*- coding: utf-8 -*-
import abc
import warnings
from functools import partial
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar, Union

import streamlit as st
from kiara.interfaces.python_api.models.info import InfoItemGroup, ItemInfo
from kiara.models.documentation import (
    AuthorsMetadataModel,
    ContextMetadataModel,
    DocumentationMetadataModel,
)
from pydantic import BaseModel, Field
from pydantic.fields import ModelField
from streamlit.runtime.state import SessionStateProxy

from kiara_plugin.streamlit.defaults import AUTO_GEN_MARKER

with warnings.catch_warnings():
    pass

from typing import TYPE_CHECKING

from streamlit.delta_generator import DeltaGenerator

if TYPE_CHECKING:
    from kiara.api import Kiara, KiaraAPI

    from kiara_plugin.streamlit.streamlit import KiaraStreamlit


class ComponentOptions(BaseModel):

    key: str = Field(
        description="The (base) key to use for this component.", default=AUTO_GEN_MARKER
    )

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

    def __init__(
        self, kiara_streamlit: "KiaraStreamlit", component_name: str, doc: Any = None
    ):

        self._kiara_streamlit: KiaraStreamlit = kiara_streamlit
        self._component_name: str = component_name
        self._st: DeltaGenerator = st  # type: ignore
        self._session_state: SessionStateProxy = st.session_state

        self._info: Union[ComponentInfo, None] = None
        if doc is not None:
            doc = DocumentationMetadataModel.create(doc)
        self._doc: Union[DocumentationMetadataModel, None] = doc

    @property
    def api(self) -> "KiaraAPI":
        return self._kiara_streamlit.api

    @property
    def info(self) -> "ComponentInfo":

        if self._info is None:
            self._info = ComponentInfo.create_from_instance(
                kiara=self._kiara_streamlit.api.context, instance=self
            )
        return self._info

    def doc(self) -> DocumentationMetadataModel:

        if self._doc is None:
            self._doc = DocumentationMetadataModel.from_class_doc(self.__class__)
        return self._doc

    @property
    def component_name(self) -> str:
        return self._component_name

    @property
    def kiara_streamlit(self) -> "KiaraStreamlit":
        return self._kiara_streamlit

    def default_key(self) -> str:
        return f"Component:{self.__class__.__name__}"

    def get_session_var(
        self, options: "ComponentOptions", *key: str, default: Any = None
    ) -> Any:

        session_key = options.get_session_key(*key)

        if session_key not in self._session_state:
            return default

        value = self._session_state[session_key]
        return value

    def set_session_var(
        self, options: "ComponentOptions", *key: str, value: Any
    ) -> None:

        session_key = options.get_session_key(*key)
        self._session_state[session_key] = value

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

        if "key" not in kwargs.keys() or AUTO_GEN_MARKER == kwargs["key"]:
            kwargs["key"] = self.default_key()

        try:
            options = self.__class__._options(**kwargs)
            return self._render(st, options)
        except Exception as e:
            import traceback

            traceback.print_exc()
            st.error(e)
            return None

    @abc.abstractmethod
    def _render(self, st: DeltaGenerator, options: COMP_OPTIONS_TYPE):
        pass

    def get_component(self, component_name: str) -> "KiaraComponent":
        result = self._kiara_streamlit.get_component(component_name)
        return result


class ArgInfo(BaseModel):
    @classmethod
    def from_field(cls, field_info: ModelField):

        python_type = str(field_info.type_)
        desc = field_info.field_info.description
        req = field_info.required
        default = field_info.default

        if field_info.outer_type_ != field_info.type_:
            python_type = str(field_info.outer_type_)

        if not desc:
            desc = "-- n/a --"
        return ArgInfo(
            python_type=python_type, description=desc, required=req, default=default
        )

    python_type: str = Field(description="The python type of this argument.")
    description: str = Field(description="The description of this argument.")
    required: bool = Field(description="Whether this argument is required.")
    default: Any = Field(description="The default value for this argument.")


class ComponentInfo(ItemInfo[KiaraComponent]):

    arguments: Dict[str, ArgInfo] = Field(
        description="The arguments for this component."
    )
    examples: List[Dict[str, Any]] = Field(
        description="The examples for this component.", default_factory=list
    )

    @classmethod
    def base_instance_class(cls) -> Type[KiaraComponent]:
        return KiaraComponent

    @classmethod
    def create_from_instance(cls, kiara: "Kiara", instance: KiaraComponent, **kwargs):
        authors_md = AuthorsMetadataModel.from_class(cls)
        doc = instance.doc()
        # python_class = PythonClass.from_class(cls)
        context = ContextMetadataModel.from_class(instance.__class__)
        type_name = instance.component_name

        options_cls = instance.__class__._options
        args = {}
        field_names = list(options_cls.__fields__.keys())
        field_names.reverse()
        for field_name in field_names:
            details = options_cls.__fields__[field_name]
            args[field_name] = ArgInfo.from_field(details)

        if hasattr(instance, "_instance_examples"):
            examples = instance._instance_examples  # type: ignore

        elif hasattr(instance.__class__, "_examples"):
            examples = instance.__class__._examples  # type: ignore
        else:
            examples = []

        info = ComponentInfo(
            type_name=type_name,
            authors=authors_md,
            documentation=doc,
            context=context,
            arguments=args,
            examples=examples,
        )
        return info


class ComponentsInfo(InfoItemGroup[ComponentInfo]):
    @classmethod
    def base_info_class(cls) -> Type[ComponentInfo]:
        return ComponentInfo
