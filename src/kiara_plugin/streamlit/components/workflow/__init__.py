# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from kiara.interfaces.python_api import Workflow
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI
KIARA_METADATA = {
    "description": "Kiara streamlit compoents to work with workflows",
    "tags": ["workflows"],
    "labels": {"package": "kiara_plugin.core_types"},
}


class WorkflowSession(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    workflow: Workflow = Field(description="The workflow instance.")


class WorkflowOptions(ComponentOptions):

    session: WorkflowSession = Field(description="The current workflow session.")


class WorkflowComponent(KiaraComponent):

    _options = WorkflowOptions
    _component_type = "workflow"

    def _render(self, st: "KiaraStreamlitAPI", options: WorkflowOptions):

        from kiara_plugin.streamlit.components.workflow.dynamic import (
            WorkflowSessionDynamic,
        )
        from kiara_plugin.streamlit.components.workflow.static import (
            WorkflowSessionStatic,
        )

        if isinstance(options.session, WorkflowSessionStatic):
            comp = self.get_component("workflow_static")
            return comp._render(st, options)
        elif isinstance(options.session, WorkflowSessionDynamic):
            comp = self.get_component("workflow_dynamic")
            return comp._render(st, options=options)
        else:
            raise Exception(f"Invalid workflow session type '{type(options.session)}'.")
