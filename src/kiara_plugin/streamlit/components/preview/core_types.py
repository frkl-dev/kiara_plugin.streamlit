# -*- coding: utf-8 -*-
from typing import Any, Dict

from kiara.models.data_types import DictModel
from kiara.models.filesystem import FileBundle
from kiara.utils.json import orjson_dumps
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components.preview import PreviewComponent, PreviewOptions


class DictPreview(PreviewComponent):

    _component_name = "dict_preview"

    @classmethod
    def get_data_type(cls) -> str:
        return "dict"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        dict_data: DictModel = _value.data

        data, schema = st.tabs(["Data", "Schema"])

        try:
            json_str = orjson_dumps(dict_data.dict_data)
        except Exception as e:
            json_str = f"Error parsing data: {e}"
        data.json(json_str)

        try:
            json_str = orjson_dumps(dict_data.data_schema)
        except Exception as e:
            json_str = f"Error parsing schema: {e}"
        schema.json(json_str)

        return


class FileBundlePreview(PreviewComponent):

    _component_name = "file_bundle_preview"

    @classmethod
    def get_data_type(cls) -> str:
        return "file_bundle"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        bundle: FileBundle = _value.data

        table: Dict[str, Any] = {}
        for file_path, file_info in bundle.included_files.items():
            table.setdefault("path", []).append(file_path)
            table.setdefault("size", []).append(file_info.size)
            table.setdefault("mime-type", []).append(file_info.mime_type)

        st.dataframe(table, use_container_width=True)

        return
