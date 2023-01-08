# -*- coding: utf-8 -*-
from kiara.interfaces.python_api import Workflow
from pydantic import BaseModel, Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent


class WorkflowSession(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    workflow: Workflow = Field(description="The workflow instance.")


class WorkflowOptions(ComponentOptions):

    session: WorkflowSession = Field(description="The current workflow session.")


class WorkflowComponent(KiaraComponent):

    _options = WorkflowOptions
    _component_type = "workflow"

    def _render(self, st: DeltaGenerator, options: WorkflowOptions):

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
