# -*- coding: utf-8 -*-
import atexit
import os
import shutil
import tempfile
import uuid
from typing import TYPE_CHECKING, Union

from kiara.models.values.value import ValueMapReadOnly
from kiara.registries.data import ValueLink
from kiara_plugin.streamlit.components.input import InputComponent, InputOptions

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class OnboardingInputOptions(InputOptions):
    pass


class FileOnboarding(InputComponent):
    """Render a text input widget."""

    _component_name = "onboard_file"
    _options = OnboardingInputOptions

    @classmethod
    def get_data_type(cls) -> str:
        return "file"

    @classmethod
    def get_default_label(cls) -> str:
        return "Select file"

    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: OnboardingInputOptions,
    ) -> Union[ValueLink, None, str, uuid.UUID]:

        callback, _key = self._create_session_store_callback(
            options, "onboard", "file", default=None
        )

        uploaded = st.file_uploader(
            label=options.label, key=_key, on_change=callback, help=options.help
        )

        if uploaded is None:
            return None

        temp_dir = tempfile.mkdtemp()

        def cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)

        atexit.register(cleanup)

        path = os.path.join(temp_dir, uploaded.name)

        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())

        inputs = {
            "source": path,
            "file_name": uploaded.name,
            "onboard_type": "local_file",
            "attach_metadata": True,
        }

        result: ValueMapReadOnly = self.api.run_job("import.file", inputs=inputs)
        result_file = result.get_value_obj("file")
        return result_file
