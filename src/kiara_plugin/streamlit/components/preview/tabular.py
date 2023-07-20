# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from kiara_plugin.streamlit.components.preview import PreviewComponent, PreviewOptions
from kiara_plugin.tabular.models.array import KiaraArray
from kiara_plugin.tabular.models.db import KiaraDatabase
from kiara_plugin.tabular.models.table import KiaraTable
from kiara_plugin.tabular.models.tables import KiaraTables

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ArrayPreview(PreviewComponent):
    """Preview a value of type 'array'."""

    _component_name = "preview_array"

    @classmethod
    def get_data_type(cls) -> str:
        return "array"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        table: KiaraArray = _value.data

        st.dataframe(table.to_pandas(), use_container_width=True)


class TablePreview(PreviewComponent):
    """Preview a value of type 'table'."""

    _component_name = "preview_table"

    _examples = [
        {"doc": "A table preview.", "args": {"value": "nodes_table"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "table"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        table: KiaraTable = _value.data

        if table:
            st.dataframe(
                table.to_pandas_dataframe(),
                use_container_width=True,
                hide_index=True,
                height=options.height,
            )
        else:
            st.write("No data available.")


class DatabasePreview(PreviewComponent):
    """Preview a value of type 'database'."""

    _component_name = "preview_database"
    _examples = [
        {"doc": "A database preview.", "args": {"value": "journals_database"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "database"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        db: KiaraDatabase = _value.data
        tabs = st.tabs(list(db.table_names))

        for idx, table_name in enumerate(db.table_names):
            # TODO: this is probably not ideal, as it always loads all tables because
            # of how tabs are implemented in streamlit
            # maybe there is an easy way to do this better, otherwise, maybe not use tabs
            table = db.get_table_as_pandas_df(table_name)
            tabs[idx].dataframe(
                table, use_container_width=True, hide_index=True, height=options.height
            )


class TablesPreview(PreviewComponent):
    """Preview a value of type 'tables'."""

    _component_name = "preview_tables"
    _examples = [
        {"doc": "A tables preview.", "args": {"value": "journals_tables"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "tables"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        tables: KiaraTables = _value.data
        tabs = st.tabs(tables.table_names)

        for idx, table_name in enumerate(tables.table_names):
            # TODO: this is probably not ideal, as it always loads all tables because
            # of how tabs are implemented in streamlit
            # maybe there is an easy way to do this better, otherwise, maybe not use tabs
            table = tables.get_table(table_name).to_pandas_dataframe()
            tabs[idx].dataframe(
                table, use_container_width=True, hide_index=True, height=options.height
            )
