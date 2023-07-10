# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Union

from kiara.interfaces.python_api import JobDesc
from kiara_plugin.streamlit.components.data_import import (
    DataImportComponent,
    DataImportOptions,
)

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class TableDataImportComponent(DataImportComponent):

    _component_name = "import_table"
    _examples = [{"doc": "The default table onboarding component.", "args": {}}]

    @classmethod
    def get_data_type(cls) -> str:
        return "table"

    def render_onboarding_page(
        self, st: "KiaraStreamlitAPI", options: DataImportOptions
    ) -> Union[None, JobDesc]:

        supported_file_types = ["csv"]

        with st.expander(label="Select a source file", expanded=True):
            key = options.create_key("onboard", "table", "onboard", "file")
            selected_value = self.get_component("input_file").render(
                st=st,
                key=key,
                add_existing_file_option=True,
                accepted_file_extensions=supported_file_types,
                show_preview=False,
            )

        with st.expander(label="Create table", expanded=True):
            key_column, value_column = st.columns([1, 5])
            with key_column:
                st.write("File content")
            with value_column:
                if selected_value:
                    st.kiara.preview_file(selected_value)
                else:
                    st.write("*-- no file selected --*")

            key_column, value_column = st.columns([1, 5])
            with key_column:
                st.write("Options")
            with value_column:
                inputs = st.kiara.operation_inputs(  # type: ignore
                    operation_id="create.table.from.file",
                    ignore_inputs=["file"],
                    profile="all",
                )

        if not selected_value:
            return None
        inputs = dict(inputs)
        inputs["file"] = selected_value

        job_desc = {
            "operation": "create.table.from.file",
            "inputs": inputs,
            "doc": "Create a table from the imported file.",
        }
        return JobDesc(**job_desc)
