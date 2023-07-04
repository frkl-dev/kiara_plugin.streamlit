# -*- coding: utf-8 -*-
import abc
from typing import TYPE_CHECKING, TypeVar, Union

from pydantic import BaseModel, Field

from kiara.models.values.value import Value
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class OnboardingOptions(ComponentOptions):

    display_style: str = Field(
        description="The display style to use for this input field.", default="default"
    )


class OnboardingResult(BaseModel):

    value: Union[Value, None] = Field(description="The onboarded value.")
    onboarding_complete: bool = Field(
        description="Whether the onboarding process is completed.", default=False
    )


ONBOARDING_OPTIONS_TYPE = TypeVar("ONBOARDING_OPTIONS_TYPE", bound=OnboardingOptions)


class OnboardingComponent(KiaraComponent[ONBOARDING_OPTIONS_TYPE]):

    _component_name = None  # type: ignore
    _examples = [{"doc": "Render the default table onboarding component.", "args": {}}]

    def _render(
        self, st: "KiaraStreamlitAPI", options: ONBOARDING_OPTIONS_TYPE
    ) -> Union[Value, None]:

        pass

    @abc.abstractmethod
    def render_onboarding_page(self) -> Union[Value, None]:
        pass


class TableOnboardingComponent(OnboardingComponent):

    _component_name = "onboard_table"
