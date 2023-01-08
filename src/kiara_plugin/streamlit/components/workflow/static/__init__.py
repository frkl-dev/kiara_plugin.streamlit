# -*- coding: utf-8 -*-
from pydantic import Field

from kiara_plugin.streamlit.components.workflow import WorkflowSession


class WorkflowSessionStatic(WorkflowSession):

    current_stage: int = Field(
        description="The current stage of the workflow.", default=1
    )
