# -*- coding: utf-8 -*-
from types import ModuleType
from typing import TYPE_CHECKING, Dict, List, Type, Union

from kiara.utils import camel_case_to_snake_case


def _cls_name_id_func(cls: Type) -> str:
    """Utility method to auto-generate a more or less nice looking id_or_alias for a class."""

    name = camel_case_to_snake_case(cls.__name__)
    if name.endswith("_component"):
        name = name[:-10]
    return name


if TYPE_CHECKING:
    from kiara_plugin.streamlit.components import KiaraComponent


def find_kiara_streamlit_components_under(
    module: Union[str, ModuleType],
) -> List[Type["KiaraComponent"]]:

    from kiara.utils.class_loading import find_subclasses_under
    from kiara_plugin.streamlit.components import KiaraComponent

    return find_subclasses_under(
        base_class=KiaraComponent,  # type: ignore
        python_module=module,
    )


def find_all_kiara_streamlit_components() -> Dict[str, Type["KiaraComponent"]]:
    """Find all [KiaraComponent][kiara_plugin.streamilt.components.KiaraComponent] subclasses via package entry points.

    TODO
    """

    from kiara.utils.class_loading import load_all_subclasses_for_entry_point
    from kiara_plugin.streamlit.components import KiaraComponent

    components = load_all_subclasses_for_entry_point(
        entry_point_name="kiara.streamlit_components",
        base_class=KiaraComponent,  # type: ignore
        type_id_key="_component_name",
        type_id_func=_cls_name_id_func,
        attach_python_metadata=True,
    )

    return components
