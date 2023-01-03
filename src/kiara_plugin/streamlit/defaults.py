# -*- coding: utf-8 -*-
import importlib
import os

from appdirs import AppDirs

kiara_stremalit_app_dirs = AppDirs("kiara-streamlit", "dharpa")

KIARA_STREAMLIT_RESOURCES_FOLDER = importlib.resources.files(
    "kiara_plugin.streamlit"
).joinpath("resources")
"""Default resources folder for this package."""

MODULE_DEV_STREAMLIT_FILE = os.path.join(
    KIARA_STREAMLIT_RESOURCES_FOLDER, "module_dev.py"
)
MODULE_INFO_UI_STREAMLIT_FILE = os.path.join(
    KIARA_STREAMLIT_RESOURCES_FOLDER, "module_info.py"
)

EXAMPLE_BASE_DIR = os.path.join(KIARA_STREAMLIT_RESOURCES_FOLDER, "examples")
TEMPLATES_BASE_DIR = os.path.join(KIARA_STREAMLIT_RESOURCES_FOLDER, "templates")

ONBOARD_MAKER_KEY = "__ONBOARD__"

PROFILE_KEYWORD = "style"
