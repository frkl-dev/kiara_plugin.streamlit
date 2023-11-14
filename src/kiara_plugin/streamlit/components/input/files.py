# -*- coding: utf-8 -*-
import atexit
import os
import shutil
import tempfile
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, Dict, List, Union

from pydantic import Field

from kiara.exceptions import KiaraException
from kiara.interfaces.python_api import JobDesc
from kiara.models.documentation import DocumentationMetadataModel
from kiara.models.filesystem import KiaraFile
from kiara.models.values.value import Value
from kiara.registries.data import ValueLink
from kiara.utils.doc import extract_doc_from_func
from kiara_plugin.streamlit.components.input import InputComponent, InputOptions

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class InputFileOptions(InputOptions):
    allowed_input_methods: Union[List[str], None] = Field(
        description="The import methods the user is allowed to choose from. Defaults to all available.",
        default=None,
    )
    add_existing_file_option: bool = Field(
        description="Add an option to select an already imported file.", default=False
    )
    show_preview: Union[bool, None] = Field(
        description="Whether to show a preview of the file contents. If not specified, the user can choose with a checkbox.",
        default=None,
    )
    accepted_file_extensions: Union[None, List[str]] = Field(
        description="A list of file extensions that are accepted. If not specified, all files are accepted.",
        default=None,
    )


FUNC_PREFIX = "render_import_file_from___"


class FileOnboarding(InputComponent):
    """Render a text input widget."""

    _component_name = "input_file"
    _options = InputFileOptions
    _examples = [{"doc": "The default file input widget.", "args": {}}]

    @classmethod
    def get_data_type(cls) -> str:
        return "file"

    @classmethod
    def get_default_label(cls) -> str:
        return "Upload file"

    @classmethod
    @lru_cache(maxsize=1)
    def get_supported_input_methods(cls) -> Dict[str, DocumentationMetadataModel]:

        result = {}
        for func_name in dir(cls):
            if func_name.startswith(FUNC_PREFIX):
                method_name = func_name[len(FUNC_PREFIX) :]
                func = getattr(cls, func_name)
                doc = extract_doc_from_func(func)
                result[method_name] = DocumentationMetadataModel.create(doc)

        return result

    def render_input_field(
        self,
        st: "KiaraStreamlitAPI",
        options: InputFileOptions,
    ) -> Union[ValueLink, None, str, uuid.UUID]:

        input_methods = self.__class__.get_supported_input_methods()
        if options.allowed_input_methods is None:
            methods_to_use = ["upload", "download"]
        else:
            methods_to_use = options.allowed_input_methods

        if options.add_existing_file_option and "existing" not in methods_to_use:
            methods_to_use.insert(0, "existing")

        method_callback, method_key = self._create_session_store_callback(
            options, "import", "file", "method"
        )

        last_value_key = f"{method_key}_last_value"
        last_value: Union[None, Value] = st.session_state.get(last_value_key, None)  # type: ignore

        if len(methods_to_use) > 1:
            method = st.radio(
                label="Choose method",
                options=methods_to_use,
                key=method_key,
                on_change=method_callback,
                format_func=lambda x: input_methods[x].description
                if input_methods[x].is_set
                else x,
            )
        else:
            method = methods_to_use[0]

        if method not in methods_to_use:
            raise ValueError(
                f"Import file method '{method}' is not supported. Supported methods are: {', '.join(methods_to_use)}."
            )

        method_func_name = FUNC_PREFIX + method
        method_func = getattr(self, method_func_name)
        kiara_file: Union[Value, None] = method_func(st, options)

        if kiara_file and not kiara_file.is_set:
            kiara_file = None

        if kiara_file:
            if last_value:
                changed = last_value.value_id != kiara_file.value_id
            else:
                changed = kiara_file is None
        else:
            changed = last_value is not None

        preview_callback, preview_key = self._create_session_store_callback(
            options, "import", "file", "preview"
        )

        if changed or kiara_file is None:
            st.session_state[last_value_key] = kiara_file  # type: ignore
            st.session_state[preview_key] = False  # type: ignore

        preview = False
        if options.show_preview is None:
            preview = st.checkbox(
                label="Preview file content",
                value=False,
                help="Preview the content of the selected file.",
                disabled=kiara_file is None,
                key=preview_key,
                on_change=preview_callback,
            )
        elif options.show_preview is True:
            with st.expander(label="Preview file content", expanded=True):
                if kiara_file:
                    st.kiara.preview(value=kiara_file)
                else:
                    st.info("No file selected.")
        else:
            preview = False

        if kiara_file is not None and preview:
            st.kiara.preview(value=kiara_file)

        return kiara_file

    def render_import_file_from___existing(
        self, st: "KiaraStreamlitAPI", options: InputFileOptions
    ) -> Union[Value, None]:
        """pick an already imported file"""

        _, existing_key = self._create_session_store_callback(
            options, "import", "file", "existing"
        )

        values = self.api.list_aliases(data_types=["file"])

        if not options.accepted_file_extensions:
            _values = dict(values)
        else:
            _values = {}
            for k, v in values.items():
                file: KiaraFile = v.data
                if file.file_extension in options.accepted_file_extensions:
                    _values[k] = v

        value: Union[Value, None] = self.get_component("pick_value").render(
            st, values=_values, key=existing_key, show_preview=False
        )

        return value

    def render_import_file_from___upload(
        self, st: "KiaraStreamlitAPI", options: InputFileOptions
    ) -> Union[Value, None]:
        """upload a file from your local file system"""

        _, upload_key = self._create_session_store_callback(
            options, "import", "file", "upload"
        )

        last_value_key = f"{upload_key}_last_value"
        last_value: Dict[str, any] = st.session_state.get(last_value_key, None)  # type: ignore

        file_types = options.accepted_file_extensions
        if not file_types:
            file_types = None
        uploaded_file = st.file_uploader(
            label=options.label, help=options.help, key=upload_key, type=file_types
        )

        if not uploaded_file:
            st.session_state[last_value_key] = None  # type: ignore
            return None

        # TODO: in some very edge cases this change detection can still go wrong
        if (
            last_value
            and last_value["uploaded_file"] == uploaded_file.name
            and last_value["size"] == uploaded_file.size
        ):
            changed = False
        else:
            changed = True

        if not changed:
            return last_value["value"]

        if not uploaded_file:
            return None

        temp_dir = tempfile.mkdtemp()

        def cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)

        atexit.register(cleanup)

        path = os.path.join(temp_dir, uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        kiara_file = KiaraFile.load_file(path, file_name=uploaded_file.name)
        value = self.api.register_data(
            kiara_file, data_type="file", reuse_existing=True
        )

        st.session_state[last_value_key] = {  # type: ignore
            "uploaded_file": uploaded_file.name,
            "size": uploaded_file.size,
            "value": value,
        }
        return value

    def render_import_file_from___download(
        self, st: "KiaraStreamlitAPI", options: InputFileOptions
    ) -> Union[Value, None]:
        """download a file from a remote location"""

        download_callback, download_key = self._create_session_store_callback(
            options, "import", "file", "download"
        )

        last_value_key = f"{download_key}_last_value"
        last_value = st.session_state.get(last_value_key, None)  # type: ignore

        with st.form(key=f"{download_key}_form"):
            url: Union[str, None] = st.text_input(
                label="Enter the URL to download the file from",
                help=options.help,
                key=download_key,
            )
            import_button = st.form_submit_button("Download")

        if not url:
            url = None

        if (last_value and last_value["url"] == url) or (
            last_value is None and url is None
        ):
            changed = False
        else:
            changed = True
            last_value = None
            st.session_state[last_value_key] = None  # type: ignore

        if not changed:
            if last_value:
                result_value: Union[Value, None] = last_value["value"]
                return result_value
            else:
                return None

        valid_url = bool(url)  # TODO: validate URL

        if not import_button:
            if last_value:
                result_value = last_value["value"]
                return result_value
            else:
                return None

        if not valid_url:
            return None

        if options.accepted_file_extensions:
            match = False
            for ext in options.accepted_file_extensions:
                if url and url.endswith(ext):
                    match = True
                    break
            if not match:
                st.error(
                    f"The selected URL does not end with any of the accepted extensions: {', '.join(options.accepted_file_extensions)}"
                )
                return None

        inputs = {"source": url, "onboard_type": "url"}

        try:
            job_desc = JobDesc(operation="import.file", inputs=inputs)
            result = st.kiara.run_job_panel(job_desc=job_desc)
        except Exception as e:
            msg = KiaraException.get_root_details(e)
            st.error(msg)
            return None

        value: Value = result.get_value_obj("file")
        st.session_state[last_value_key] = {"url": url, "value": value}  # type: ignore

        return value
