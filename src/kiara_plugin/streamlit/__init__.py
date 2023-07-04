# -*- coding: utf-8 -*-

"""Top-level package for kiara_plugin.streamlit."""
import os
import typing
import warnings
from typing import Dict, Union

# import streamlit as st
from kiara.utils.class_loading import (
    KiaraEntryPointItem,
    find_data_types_under,
    find_kiara_model_classes_under,
    find_kiara_modules_under,
    find_kiara_renderers_under,
    find_pipeline_base_path_for_module,
)
from kiara_plugin.streamlit.components.modals import KiaraStreamlitModal
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
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = get_distribution(dist_name).version
    except DistributionNotFound:

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

    if page_config is not None:
        st.set_page_config(**page_config)

    @st.cache_resource
    def get_ktx() -> "KiaraStreamlit":
        # print("CREATE KIARA STREAMLIT")
        ktx = KiaraStreamlit(
            context_config=context_config, runtime_config=runtime_config
        )
        return ktx

    if not hasattr(st, "kiara"):
        ktx = get_ktx()
        setattr(st, "kiara", ktx)

    modal = st.session_state.get(WANTS_MODAL_MARKER_KEY, None)
    if modal is not None:

        if not issubclass(modal.__class__, KiaraStreamlitModal):
            raise Exception(
                f"Invalid modal object in session state, must implement the 'KiaraStreamlitModal' protocol, not: '{type(modal)}'"
            )

        modal_finished = modal.show_modal(st=st)
        if modal_finished:
            st.session_state.pop(WANTS_MODAL_MARKER_KEY)
            st.experimental_rerun()
        else:
            st.stop()

    return st  # type: ignore


kiara_streamlit_init = init
