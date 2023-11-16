# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Mapping, Union

from pydantic import BaseModel, ConfigDict, Field

from kiara_plugin.streamlit.components import ComponentOptions

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ModelComponentOptions(ComponentOptions):
    """Options for rendering a generic model."""

    # TODO: can this stay, or should I refactor the 'model_instance' attribute name?
    model_config = ConfigDict(protected_namespaces=())

    model_instance: BaseModel = Field(description="The model to render.")


# def create_recursive_table_from_model_object(
#     model: BaseModel,
#     render_config: Union[Mapping[str, Any], None] = None,
# ):
#
#     if render_config is None:
#         render_config = {}
#
#     model_cls = model.__class__
#
#     table = {
#         "Field": [],
#         "Type": [],
#         "Value": [],
#         "Description": [],
#     }
#
#     props = model_cls.schema().get("properties", {})
#
#     for field_name in sorted(model_cls.__fields__.keys()):
#
#         data = getattr(model, field_name)
#         p = props.get(field_name, None)
#         p_type = None
#         desc = None
#         if p is not None:
#             p_type = p.get("type", None)
#             # TODO: check 'anyOf' keys
#             desc = p.get("description", None)
#
#         if p_type is None:
#             p_type = "-- n/a --"
#
#         if isinstance(data, BaseModel):
#             data_renderable = create_recursive_table_from_model_object(data, render_config=render_config)
#         elif isinstance(data, Mapping):
#             _data_renderable = {}
#             for k, v in data.items():
#                 if isinstance(v, BaseModel):
#                     _data_renderable[k] = create_recursive_table_from_model_object(
#                         model=v, render_config=render_config
#                     )
#                 else:
#                     _data_renderable[k] = v
#             data_renderable = _data_renderable
#         else:
#             data_renderable = data
#             # sub_model = create_recursive_table_from_model_object(
#             #     data, render_config={"show_lines": True, "show_header": False}
#             # )
#             # data_renderable = None
#
#
#         table["Field"].append(field_name)
#         table["Type"].append(p_type)
#         table["Value"].append(data_renderable)
#         table["Description"].append(desc)
#
#     return table
#
def write_generic_data(
    st: "KiaraStreamlitAPI", data: Any, prefix: Union[str, None] = None
):
    """Try to write generic data."""

    if isinstance(data, BaseModel):

        field_names = sorted(data.__fields__.keys())

        if len(field_names) > 1:
            for field_name in field_names:
                key_col, val_col = st.columns([1, 5])
                field_data = getattr(data, field_name)
                with key_col:
                    if prefix:
                        _text = f"{prefix}.{field_name}"
                    else:
                        _text = field_name
                    st.write(f"**{_text}**")
                with val_col:
                    write_generic_data(st, field_data)
        else:
            write_generic_data(st, getattr(data, field_names[0]), prefix=field_names[0])

    elif isinstance(data, Mapping):
        for k, v in data.items():
            key_col, val_col = st.columns([1, 4])
            with key_col:
                if not prefix:
                    st.write(f"**{k}**")
                else:
                    st.write(f"**{prefix}.{k}**")
            with val_col:
                write_generic_data(st, v)
    else:
        st.write(data)


def create_recursive_table_from_model_object(
    model: BaseModel,
    render_config: Union[Mapping[str, Any], None] = None,
):

    if render_config is None:
        render_config = {}

    model_cls = model.__class__

    table = {}

    props = model_cls.schema().get("properties", {})

    for field_name in sorted(model_cls.model_fields.keys()):

        data = getattr(model, field_name)
        p = props.get(field_name, None)
        p_type = None
        if p is not None:
            p_type = p.get("type", None)
            # TODO: check 'anyOf' keys
            p.get("description", None)

        if p_type is None:
            p_type = "-- n/a --"

        if isinstance(data, BaseModel):
            data_renderable = create_recursive_table_from_model_object(
                data, render_config=render_config
            )
        elif isinstance(data, Mapping):
            _data_renderable = {}
            for k, v in data.items():
                if isinstance(v, BaseModel):
                    _data_renderable[k] = create_recursive_table_from_model_object(
                        model=v, render_config=render_config
                    )
                else:
                    _data_renderable[k] = v
            data_renderable = _data_renderable
        else:
            data_renderable = data
            # sub_model = create_recursive_table_from_model_object(
            #     data, render_config={"show_lines": True, "show_header": False}
            # )
            # data_renderable = None

        # table[field_name] = {
        #     "data": data_renderable,
        #     "type": p_type,
        #     "description": desc,
        # }
        table[field_name] = data_renderable

    return table


# class ModelComponent(KiaraComponent[ModelComponentOptions]):
#     """Component for rendering generic model data."""
#
#     _component_name = "display_model"
#     _options = ModelComponentOptions
#
#     def _render(self, st: "KiaraStreamlitAPI", options: ModelComponentOptions):
#
#         model: Value = options.model_instance  # type: ignore
#         table_data = create_recursive_table_from_model_object(model.data)
#
#         name_col, val_col = st.columns([1,4])
#
#         for key, value in table_data.items():
#
#             with name_col:
#                 st.write(key)
#
#             with val_col:
#                 if isinstance(value, (Mapping, List)):
#                     st.json(value, expanded=False)
#                 else:
#                     st.write(value)
