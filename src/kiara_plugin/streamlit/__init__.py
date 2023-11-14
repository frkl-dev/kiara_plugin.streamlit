# -*- coding: utf-8 -*-

"""Top-level package for kiara_plugin.streamlit."""
import os
import typing
import warnings
from typing import Dict, List, Union

# import streamlit as st
from kiara.utils.class_loading import (
    KiaraEntryPointItem,
    find_data_types_under,
    find_kiara_model_classes_under,
    find_kiara_modules_under,
    find_kiara_renderers_under,
    find_pipeline_base_path_for_module,
)
from kiara_plugin.streamlit.defaults import WANTS_MODAL_MARKER_KEY

# import kiara_plugin.streamlit.utils.monkey_patches
from kiara_plugin.streamlit.utils.class_loading import (
    find_kiara_streamlit_components_under,
)

if typing.TYPE_CHECKING:
    from kiara.context import KiaraContextConfig, KiaraRuntimeConfig
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI
    from kiara_plugin.streamlit.streamlit import KiaraStreamlit


__author__ = """Markus Binsteiner"""
__email__ = "markus@frkl.io"
warnings.simplefilter(action="ignore", category=FutureWarning)


KIARA_METADATA = {
    "authors": [{"name": __author__, "email": __email__}],
    "description": "Kiara modules for: streamlit",
    "references": {
        "source_repo": {
            "desc": "The module package git repository.",
            "url": "https://github.com/DHARPA-Project/kiara_plugin.streamlit",
        },
        "documentation": {
            "desc": "The url for the module package documentation.",
            "url": "https://DHARPA-Project.github.io/kiara_plugin.streamlit/",
        },
    },
    "tags": ["streamlit"],
    "labels": {"package": "kiara_plugin.streamlit"},
}

find_modules: KiaraEntryPointItem = (
    find_kiara_modules_under,
    "kiara_plugin.streamlit.modules",
)
find_model_classes: KiaraEntryPointItem = (
    find_kiara_model_classes_under,
    "kiara_plugin.streamlit.models",
)
find_data_types: KiaraEntryPointItem = (
    find_data_types_under,
    "kiara_plugin.streamlit.data_types",
)
find_pipelines: KiaraEntryPointItem = (
    find_pipeline_base_path_for_module,
    "kiara_plugin.streamlit.pipelines",
    KIARA_METADATA,
)
find_kiara_streamlit_components: KiaraEntryPointItem = (
    find_kiara_streamlit_components_under,
    "kiara_plugin.streamlit.components",
)
find_renderer_classes: KiaraEntryPointItem = (
    find_kiara_renderers_under,
    "kiara_plugin.streamlit.renderers",
)


def get_version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = version(dist_name)
    except PackageNotFoundError:

        try:
            version_file = os.path.join(os.path.dirname(__file__), "version.txt")

            if os.path.exists(version_file):
                with open(version_file, encoding="utf-8") as vf:
                    __version__ = vf.read()
            else:
                __version__ = "unknown"

        except (Exception):
            pass

        if __version__ is None:
            __version__ = "unknown"

    return __version__


def init(
    context_config: Union[None, "KiaraContextConfig"] = None,
    runtime_config: Union[None, "KiaraRuntimeConfig"] = None,
    page_config: Union[None, Dict[str, typing.Any]] = None,
) -> "KiaraStreamlitAPI":

    import kiara_plugin.streamlit.utils.monkey_patches  # noqa
    import streamlit as st
    from kiara_plugin.streamlit.streamlit import KiaraStreamlit
    from kiara_plugin.streamlit.components.modals import ModalRequest

    if page_config is not None:
        st.set_page_config(**page_config)  # type: ignore[attr-defined]

    @st.cache_resource  # type: ignore[attr-defined]
    def get_ktx() -> "KiaraStreamlit":
        # print("CREATE KIARA STREAMLIT")
        ktx = KiaraStreamlit(
            context_config=context_config, runtime_config=runtime_config
        )
        return ktx

    if not hasattr(st, "kiara"):
        ktx = get_ktx()
        setattr(st, "kiara", ktx)

    if WANTS_MODAL_MARKER_KEY not in st.session_state.keys():  # type: ignore[attr-defined]
        st.session_state[WANTS_MODAL_MARKER_KEY] = []  # type: ignore[attr-defined]

    modal_requests: List[ModalRequest] = st.session_state[WANTS_MODAL_MARKER_KEY]  # type: ignore[attr-defined]

    if modal_requests:
        modal_request = modal_requests[-1]

        if not isinstance(modal_request, ModalRequest):
            raise Exception(
                f"Invalid modal object in session state, must inherit from 'ModalRequest': '{type(modal_request)}'"
            )

        modal_request.modal.show_modal(st=st, request=modal_request)  # type: ignore
        if modal_request.result.modal_finished:
            st.session_state[WANTS_MODAL_MARKER_KEY].pop()  # type: ignore[attr-defined]
            st.experimental_rerun()  # type: ignore[attr-defined]
        else:
            st.stop()  # type: ignore[attr-defined]

    return st  # type: ignore


kiara_streamlit_init = init
