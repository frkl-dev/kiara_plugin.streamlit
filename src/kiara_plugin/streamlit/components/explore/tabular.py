# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

import pygwalker as pyg

import streamlit.components.v1 as components
from kiara_plugin.streamlit.components.preview import PreviewComponent, PreviewOptions
from kiara_plugin.tabular.models.db import KiaraDatabase
from kiara_plugin.tabular.models.tables import KiaraTable, KiaraTables

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class TableExplorer(PreviewComponent):
    """Explore a 'table' value visually."""

    _component_name = "explore_table"

    _examples = [
        {"doc": "A table explorer component.", "args": {"value": "nodes_table"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "table"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):
        _value = self.api.get_value(options.value)
        table: KiaraTable = _value.data

        df = table.to_polars_dataframe()  # noqa
        pyg_html = pyg.walk(df, return_html=True)
        components.html(pyg_html, height=1000, scrolling=True)


class DatabasePreview(PreviewComponent):
    """Preview a value of type 'database'."""

    _component_name = "explore_database"
    _examples = [
        {"doc": "A database preview.", "args": {"value": "journals_database"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "database"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        db: KiaraDatabase = _value.data

        table_names = list(db.table_names)

        selected_table = st.selectbox("Select table", table_names)
        if not selected_table:
            return

        table = db.get_table_as_pandas_df(selected_table)

        pyg_html = pyg.walk(table, return_html=True)
        components.html(pyg_html, height=1000, scrolling=True)


class TablesPreview(PreviewComponent):
    """Preview a value of type 'tables'."""

    _component_name = "explore_tables"
    _examples = [
        {"doc": "A tables preview.", "args": {"value": "journals_tables"}},
    ]

    @classmethod
    def get_data_type(cls) -> str:
        return "database"

    def render_preview(self, st: "KiaraStreamlitAPI", options: PreviewOptions):

        _value = self.api.get_value(options.value)
        tables: KiaraTables = _value.data

        selected_table = st.selectbox("Select table", tables.table_names)

        if not selected_table:
            return

        table = tables.get_table(selected_table).to_polars_dataframe()

        pyg_html = pyg.walk(table, return_html=True)
        components.html(pyg_html, height=1000, scrolling=True)
