# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Mapping

from pydantic import Field

from kiara.api import ValueSchema
from kiara.utils.output import create_dict_from_field_schemas
from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class FieldsInfoOptions(ComponentOptions):

    fields: Mapping[str, ValueSchema] = Field(
        description="The fields and their schema."
    )


class FieldsInfo(KiaraComponent[FieldsInfoOptions]):
    """Display information about a set of input fields.

    This is mostly used to display the input requirements of an operation or pipeline to users.
    """

    _component_name = "fields_info"
    _options = FieldsInfoOptions

    _examples = [
        {
            "doc": "Render a table with information about the provided input field items.\n\nIn most cases, you would not build the field schemas up yourself, but use already existing 'inputs_schema' object attached to operations or workflows.",
            "args": {
                "fields": {
                    "text_field": {
                        "type": "string",
                        "doc": "A text field.",
                    },
                    "number_field": {"type": "integer", "doc": "A number."},
                }
            },
        }
    ]

    def _render(self, st: "KiaraStreamlitAPI", options: FieldsInfoOptions):

        import pandas as pd

        fields = options.fields
        fields_data = create_dict_from_field_schemas(fields)
        dataframe = pd.DataFrame(fields_data, columns=list(fields_data.keys()))
        dataframe.set_index("field_name", inplace=True)  # noqa
        st.table(dataframe)
