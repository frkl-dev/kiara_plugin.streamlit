# -*- coding: utf-8 -*-
import importlib_resources
from appdirs import AppDirs

kiara_stremalit_app_dirs = AppDirs("kiara-streamlit", "dharpa")

KIARA_STREAMLIT_RESOURCES_FOLDER = importlib_resources.files(  # type: ignore
    "kiara_plugin.streamlit"
).joinpath("resources")

"""Default resources folder for this package."""

ONBOARD_MAKER_KEY = "__ONBOARD__"

NO_VALUE_MARKER = "-- no value --"

NO_LABEL_MARKER = "-- no label --"

AUTO_GEN_MARKER = "-- generated --"
