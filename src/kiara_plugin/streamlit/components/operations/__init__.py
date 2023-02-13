# -*- coding: utf-8 -*-
from typing import Union

from kiara.api import ValueMap
from kiara.exceptions import KiaraException
from kiara.interfaces.python_api import OperationInfo
from kiara.models.module.operation import Operation
from pydantic import Field, validator
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent


class OperationProcessOptions(ComponentOptions):

    operation_id: str = Field(description="The id of the operation to use.")

    @validator("operation_id")
    def _validate_operation_id(cls, v: str) -> str:

        if isinstance(v, str):
            return v
        elif isinstance(v, Operation):
            return v.operation_id
        elif isinstance(v, OperationInfo):
            return v.operation.operation_id
        else:
            raise ValueError(f"Invalid type for operation id: {type(v)}.")


class OperationProcessPanel(KiaraComponent[OperationProcessOptions]):

    _component_name = "process_operation"
    _options = OperationProcessOptions

    def _render(
        self, st: DeltaGenerator, options: OperationProcessOptions
    ) -> Union[ValueMap, None]:

        comp = self.get_component("operation_inputs")
        operation_inputs: ValueMap = comp.render_func(st)(
            operation_id=options.operation_id,
            key=options.create_key("inputs", options.operation_id),
        )

        invalid = operation_inputs.check_invalid()

        if invalid:
            txt = "Invalid inputs:\n\n"
            for k, v in invalid.items():
                txt += f"- {k}: {v}\n"
            st.error(txt)

        process_btn = st.button("Process", disabled=bool(invalid))
        result: Union[None, ValueMap] = None
        if process_btn:
            with st.container():
                with self._st.spinner("Processing..."):  # type: ignore
                    try:
                        result = self.api.run_job(
                            operation=options.operation_id, inputs=operation_inputs
                        )
                    except Exception as e:
                        st.error(KiaraException.get_root_details(e))

        if result is None:
            return None
        else:
            comp = self.get_component("value_map_preview")
            comp.render_func(st)(
                value_map=dict(result),
                key=options.create_key("result", options.operation_id),
            )

        return result
