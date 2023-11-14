# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Dict, Union

from pydantic import Field, field_validator

from kiara.api import ValueMap
from kiara.exceptions import KiaraException
from kiara.interfaces.python_api import JobDesc, OperationInfo
from kiara.models.module.operation import Operation
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class RunJobOptions(ComponentOptions):

    reuse_previous_result: bool = Field(
        description="Whether to cache previous results and return them straight away.",
        default=True,
    )
    add_save_option: bool = Field(
        description="Add a save option to the preview (if preview enabled).",
        default=False,
    )
    preview_result: bool = Field(
        description="Whether to preview the result.", default=False
    )
    run_instantly: bool = Field(
        description="Whether to not display a 'Process' button and run the job instantly.",
        default=False,
    )
    disabled: bool = Field(
        description="Whether the component is disabled.", default=False
    )
    job_desc: Union[JobDesc, None] = Field(
        description="The description of the job to run."
    )


class RunJobPanel(KiaraComponent[RunJobOptions]):

    _component_name = "run_job_panel"
    _options = RunJobOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: RunJobOptions
    ) -> Union[ValueMap, None]:

        job_desc = options.job_desc
        disabled = options.disabled or job_desc is None

        has_previous_result = False
        if job_desc and options.reuse_previous_result:
            if st.kiara.has_job_result(job_desc):
                has_previous_result = True

        if not options.run_instantly:
            process_btn = st.button("Process", disabled=disabled or has_previous_result)
            if has_previous_result:
                process_btn = True
        else:
            process_btn = True

        result: Union[None, ValueMap] = None
        if process_btn:
            if disabled:
                st.write("This panel is disabled, not running job...")
            else:
                with st.container():
                    with self._st.spinner("Processing..."):  # type: ignore
                        try:
                            result = st.kiara.run_job(
                                job=job_desc,
                                reuse_previous=options.reuse_previous_result,
                            )
                        except Exception as e:
                            st.error(KiaraException.get_root_details(e))

        if result is None:
            return None
        elif options.preview_result:
            comp = self.get_component("value_map_preview")
            st.write("**Result preview**")
            comp.render_func(st)(
                value_map=dict(result),
                key=options.create_key("result", job_desc.operation),  # type: ignore
                add_save_option=options.add_save_option,
            )

        return result


class OperationProcessOptions(ComponentOptions):
    reuse_previous_result: bool = Field(
        description="Whether to cache previous results and return them straight away.",
        default=False,
    )

    module_config: Union[Dict[str, Any], None] = Field(
        description="Optional module config.", default=None
    )
    fixed_inputs: Dict[str, Any] = Field(
        description="Use those fixed values and Don't render input widgets for their fields.",
        default_factory=dict,
    )
    operation_id: str = Field(description="The id of the operation to use.")

    @field_validator("operation_id")
    @classmethod
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

    _component_name = "operation_process_panel"
    _options = OperationProcessOptions

    def _render(
        self, st: "KiaraStreamlitAPI", options: OperationProcessOptions
    ) -> Union[ValueMap, None]:

        comp = self.get_component("operation_inputs")
        operation_inputs: ValueMap = comp.render_func(st)(
            operation_id=options.operation_id,
            module_config=options.module_config,
            key=options.create_key("inputs", options.operation_id),
        )

        invalid = operation_inputs.check_invalid()

        if invalid:
            txt = "Invalid inputs:\n\n"
            for k, v in invalid.items():
                txt += f"- {k}: {v}\n"
            st.error(txt)

        job_desc = JobDesc(
            operation=options.operation_id, inputs=dict(operation_inputs)
        )
        _key = options.create_key("process_panel", job_desc.operation)

        process_btn = st.button("Process", disabled=bool(invalid), key=f"{_key}_btn")
        result: Union[None, ValueMap] = None
        if process_btn:
            with st.container():
                with self._st.spinner("Processing..."):  # type: ignore

                    try:
                        result = self.kiara_streamlit.run_job_panel(
                            job_desc=job_desc,
                            reuse_previous_result=options.reuse_previous_result,
                            key=f"{_key}_run_job_panel",
                            run_instantly=True,
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
