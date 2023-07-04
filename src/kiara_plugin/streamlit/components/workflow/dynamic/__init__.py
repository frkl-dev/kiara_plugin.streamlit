# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Dict, List, Union

from pydantic import Field

from kiara.api import Value
from kiara.interfaces.python_api import OperationInfo, Workflow
from kiara_plugin.streamlit.components.workflow import WorkflowSession

if TYPE_CHECKING:
    pass

LEFT_COLUMN = 1
RIGHT_COLUMN = 4


class WorkflowSessionDynamic(WorkflowSession):

    initial_value: Union[None, Value] = Field(
        description="The initial value for workflow.", default=None
    )
    current_value: Union[None, Value] = Field(
        description="The current value for the next step.", default=None
    )

    input_values: Dict[int, Dict[str, Value]] = Field(
        description="The values that are already set for this workflow.",
        default_factory=dict,
    )
    output_values: Dict[int, Dict[str, Value]] = Field(
        description="The values that are already set for this workflow.",
        default_factory=dict,
    )
    operations: Dict[int, OperationInfo] = Field(
        description="The operations for each step.", default_factory=dict
    )
    pipeline_steps: List[str] = Field(
        description="The steps that were added to this workflow, in order.",
        default_factory=list,
    )
    last_step_processed: bool = Field(
        description="Whether the last step was valid.", default=False
    )
    last_operation: Union[None, OperationInfo] = Field(
        description="The last operation that was selected.", default=None
    )
    current_outputs: Union[None, Dict[str, Value]] = Field(
        description="The outputs of the last operation (if applicable).", default=None
    )

    def reset(self, workflow: Workflow):

        self.initial_value = None
        self.current_value = None
        self.input_values = {}
        self.output_values = {}
        self.operations = {}
        self.pipeline_steps = []
        self.workflow = workflow
        self.last_step_processed = False
        self.current_outputs = None
        self.last_operation = None
