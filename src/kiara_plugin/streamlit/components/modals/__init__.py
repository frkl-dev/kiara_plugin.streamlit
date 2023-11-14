# -*- coding: utf-8 -*-
import abc
from typing import TYPE_CHECKING, Protocol, Union, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ModalConfig(BaseModel):

    request_alias: Union[bool, None] = Field(
        description="If 'True', require an alias to be provided. If 'None', the alias field will be rendered, but the user can choose to ignore it.",
        default=False,
    )
    store_alias_key: Union[str, None] = Field(
        description="If provided, use store the new alias under the given key. Ignored if 'require_alias' is False",
        default=None,
    )
    store_value_key: Union[str, None] = Field(
        description="If provided, use store the new value under the given key.",
        default=None,
    )


class ModalResult(BaseModel):

    modal_finished: bool = Field(
        description="Whether the modal was finished.", default=False
    )


class ModalRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    modal: "KiaraStreamlitModal" = Field(description="The modal component to show.")
    config: ModalConfig = Field(
        description="The configuration to use when calling the 'show_modal' method on the modal instance."
    )
    result: ModalResult = Field(
        description="Placeholder instance for the result of the modal component."
    )


@runtime_checkable
class KiaraStreamlitModal(Protocol):
    @abc.abstractmethod
    def show_modal(self, st: "KiaraStreamlitAPI", request: ModalRequest) -> bool:
        pass


ModalRequest.model_rebuild()
