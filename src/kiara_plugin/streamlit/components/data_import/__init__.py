# -*- coding: utf-8 -*-
import abc
from typing import TYPE_CHECKING, Type, TypeVar, Union

from pydantic import BaseModel, Field

from kiara.defaults import DEFAULT_NO_DESC_VALUE
from kiara.interfaces.python_api import JobDesc
from kiara.models.values.value import Value, ValueMap
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.components.modals import ModalRequest
from kiara_plugin.streamlit.defaults import NO_LABEL_MARKER

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class DataImportOptions(ComponentOptions):

    reuse_previous_preview_results: bool = Field(
        description="Whether to cache previous preview results and display the preview straight away.",
        default=True,
    )
    display_style: str = Field(
        description="The display style to use for this input field.", default="default"
    )
    help: Union[str, None] = Field(
        description="The help to display for this input field.",
        default=DEFAULT_NO_DESC_VALUE,
    )
    label: str = Field(
        description="The label to use for the input field.", default=NO_LABEL_MARKER
    )
    result_field: Union[str, None] = Field(
        description="The name of the field to use to pick the result value from the job result that is run. Defaults to data type name.",
        default=None,
    )


class DataImportResult(BaseModel):

    value: Union[Value, None] = Field(None, description="The value that was onboarded.")
    is_finished: bool = Field(description="Whether the onboarding process is finished.")


ONBOARDING_OPTIONS_TYPE = TypeVar("ONBOARDING_OPTIONS_TYPE", bound=DataImportOptions)


class DataImportComponent(KiaraComponent[ONBOARDING_OPTIONS_TYPE]):

    _component_name = None  # type: ignore
    _examples = [{"doc": "Render the default table onboarding component.", "args": {}}]
    _options: Type[DataImportOptions] = DataImportOptions  # type: ignore

    def _render(
        self, st: "KiaraStreamlitAPI", options: ONBOARDING_OPTIONS_TYPE
    ) -> Union[Value, None]:

        job_desc = self.render_onboarding_page(st=st, options=options)
        if job_desc:
            job_result = st.kiara.run_job_panel(
                job_desc=job_desc,
                reuse_previous_result=options.reuse_previous_preview_results,
            )
        else:
            job_result = None

        result_value = None
        if job_result:

            field_name = options.result_field
            if not field_name:
                field_name = self.get_data_type()

            if field_name not in job_result.field_names:
                raise Exception(
                    f"Can't pick field '{field_name}' from result of import operation. Available field names: {', '.join(job_result.field_names)}. This is most likely a bug."
                )

            result_value = job_result.get_value_obj(field_name)

        return result_value

    @classmethod
    @abc.abstractmethod
    def get_data_type(cls) -> str:
        """Return the data type this component can import."""

    @abc.abstractmethod
    def render_onboarding_page(
        self, st: "KiaraStreamlitAPI", options: DataImportOptions
    ) -> Union[None, JobDesc]:
        """Render a page that onboards a value.

        Arguments:
            st: The KiaraStreamlitAPI instance.
            options: The options for the onboarding component.
        """

    def create_modal_options(
        self, st: "KiaraStreamlitAPI", request: ModalRequest
    ) -> DataImportOptions:

        default_options = self._options()
        return default_options

    def show_modal(self, st: "KiaraStreamlitAPI", request: ModalRequest) -> None:

        options = self.create_modal_options(st=st, request=request)
        _key = options.create_key("import", self.get_data_type(), "modal")

        job_desc = self.render_onboarding_page(st=st, options=options)

        reuse_results = options.reuse_previous_preview_results

        if job_desc and reuse_results:
            previous_result = st.kiara.get_previous_job_result(job=job_desc)
            if previous_result:
                field_name = options.result_field
                if not field_name:
                    field_name = self.get_data_type()
                result_value = previous_result.get_value_obj(field_name)
            else:
                result_value = None
        else:
            result_value = None

        preview_container, button_area = st.columns([5, 1])

        submit = False
        with button_area:
            cancel = st.button(
                "Cancel", key=f"{_key}_cancel_button", use_container_width=True
            )
            if cancel:
                request.result.modal_finished = True
                return

            preview = st.button(
                "Preview",
                key=f"{_key}_preview_button",
                disabled=not job_desc or result_value is not None,
                use_container_width=True,
            )

            save_placeholder = st.empty()

        with preview_container:
            preview_placeholder = st.empty()

        if not result_value:
            if not job_desc or (not preview and not submit):
                if result_value is None:
                    preview_placeholder.write("-- no value --")

            else:
                job_result: ValueMap = st.kiara.run_job_panel(
                    job_desc=job_desc,
                    run_instantly=True,
                    reuse_previous_result=reuse_results,
                )

                if not job_result:
                    preview_placeholder.write("-- no value --")
                    return

                field_name = options.result_field
                if not field_name:
                    field_name = self.get_data_type()

                if field_name not in job_result.field_names:
                    raise Exception(
                        f"Can't pick field '{field_name}' from result of import operation. Available field names: {', '.join(job_result.field_names)}. This is most likely a bug."
                    )

                result_value = job_result.get_value_obj(field_name)

        if result_value is not None:
            with preview_placeholder:
                st.kiara.preview(result_value)

        with save_placeholder:
            with st.form("Save & import"):
                alias = st.text_input(
                    "Alias",
                    help=f"The alias to save the imported {self.get_data_type()} value as.",
                    key=f"{_key}_alias_field",
                )
                submit = st.form_submit_button("Import", disabled=result_value is None)

        if submit:
            if not alias:
                with button_area:
                    st.error("No alias specified.")
            elif not result_value:
                st.error("No value to import.")
            else:

                self.api.store_value(result_value, alias=alias, allow_overwrite=True)
                request.result.modal_finished = True
                request.result.value = result_value  # type: ignore
                request.result.alias = alias  # type: ignore

                if request.config.store_alias_key:
                    st.session_state[request.config.store_alias_key] = alias  # type: ignore
                if request.config.store_value_key:
                    st.session_state[request.config.store_value_key] = result_value  # type: ignore
