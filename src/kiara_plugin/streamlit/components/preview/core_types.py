# -*- coding: utf-8 -*-
from typing import Any, Dict

from kiara.models.data_types import KiaraDict
from kiara.models.filesystem import FileBundle, FileModel
from kiara.utils.json import orjson_dumps
from kiara_plugin.core_types.models import KiaraList
from kiara_plugin.streamlit.components.preview import PreviewComponent, PreviewOptions
from streamlit.delta_generator import DeltaGenerator


class DictPreview(PreviewComponent):
    """Preview a value of type 'dict'."""

    _component_name = "preview_dict"

    @classmethod
    def get_data_type(cls) -> str:
        return "dict"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        dict_data: KiaraDict = _value.data

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


class ListPreview(PreviewComponent):
    """Preview a value of type 'list'."""

    _component_name = "preview_list"

    @classmethod
    def get_data_type(cls) -> str:
        return "list"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        list_data: KiaraList = _value.data

        data, schema = st.tabs(["Data", "Schema"])

        try:
            json_str = orjson_dumps(list_data.list_data)
        except Exception as e:
            json_str = f"Error parsing data: {e}"
        data.json(json_str)

        try:
            json_str = orjson_dumps(list_data.item_schema)
        except Exception as e:
            json_str = f"Error parsing schema: {e}"
        schema.json(json_str)


class FileBundlePreview(PreviewComponent):
    """Preview a value of type 'file_bundle'."""

    _component_name = "preview_file_bundle"

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


class FilePreview(PreviewComponent):
    """Preview a value of type 'file'."""

    _component_name = "preview_file"

    @classmethod
    def get_data_type(cls) -> str:
        return "file"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        file_model: FileModel = _value.data

        table: Dict[str, Any] = {"key": [], "value": []}
        table["key"].append("path")
        table["value"].append(file_model.path)
        table["key"].append("size")
        table["value"].append(file_model.size)
        table["key"].append("mime-type")
        table["value"].append(file_model.mime_type)
        table["key"].append("content")
        table["value"].append(file_model.read_text())
        st.table(table)

        # st.table(table, use_container_width=True)


class BooleanPreview(PreviewComponent):
    """Preview a value of type 'boolean'."""

    _component_name = "preview_boolean"

    @classmethod
    def get_data_type(self) -> str:
        return "boolean"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        if _value.data is True:
            st.write("true")
        else:
            st.write("false")


class StringPreview(PreviewComponent):
    """Preview a value of type 'string'."""

    _component_name = "preview_string"

    @classmethod
    def get_data_type(self) -> str:
        return "string"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        text = _value.data
        st.text_area(
            label="The string content",
            value=text,
            disabled=True,
            label_visibility="hidden",
        )


class IntegerPreview(PreviewComponent):
    """Preview a value of type 'integer'."""

    _component_name = "preview_integer"

    @classmethod
    def get_data_type(self) -> str:
        return "integer"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        text = _value.data
        st.text_input(label="The integer value", value=str(text), disabled=True)


class FloatPreview(PreviewComponent):
    """Preview a value of type 'float'."""

    _component_name = "preview_float"

    @classmethod
    def get_data_type(self) -> str:
        return "float"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        _value = self.api.get_value(options.value)
        text = _value.data
        st.text_input(label="The float value", value=str(text), disabled=True)


class NonePreview(PreviewComponent):
    """Preview a none-type value, you should not need this'."""

    _component_name = "preview_none"

    @classmethod
    def get_data_type(self) -> str:
        return "none"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions) -> None:

        st.write("-- value not set --")
