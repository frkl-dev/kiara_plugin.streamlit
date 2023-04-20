# -*- coding: utf-8 -*-
import warnings
from typing import List, Union

import pandas as pd
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder

from streamlit.delta_generator import DeltaGenerator


def create_list_component(
    st: DeltaGenerator,
    key: str,
    title: str,
    items: List[str],
    height: Union[None, int] = None,
    default: Union[str, None] = None,
) -> Union[None, str]:

    list_items = pd.DataFrame({title: items})
    builder = GridOptionsBuilder.from_dataframe(list_items)
    builder.configure_selection(selection_mode="single", use_checkbox=False)
    grid_options = builder.build()
    _key = f"{key}_component_list"

    selected_item = None

    if hasattr(st, "__enter__"):
        with st:
            with warnings.catch_warnings():
                method_list = AgGrid(
                    list_items,
                    height=height,
                    gridOptions=grid_options,
                    key=_key,
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                )
                if method_list.selected_rows:
                    selected_item = method_list.selected_rows[0][title]
    else:
        with warnings.catch_warnings():
            method_list = AgGrid(
                list_items,
                height=height,
                gridOptions=grid_options,
                key=_key,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            )
            if method_list.selected_rows:
                selected_item = method_list.selected_rows[0][title]

    return selected_item
