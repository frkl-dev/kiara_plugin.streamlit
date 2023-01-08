# -*- coding: utf-8 -*-
from typing import TypeVar

from pydantic import Field

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.workflow.static import WorkflowSessionStatic


class StaticWorkflowOptions(ComponentOptions):

    session: WorkflowSessionStatic = Field(description="The current workflow session.")


STATIC_WORKFLOW_OPTIONS_TYPE = TypeVar(
    "STATIC_WORKFLOW_OPTIONS_TYPE", bound=StaticWorkflowOptions
)


class StaticWorkflowComponent(KiaraComponent[STATIC_WORKFLOW_OPTIONS_TYPE]):

    _options = StaticWorkflowOptions  # type: ignore
