# -*- coding: utf-8 -*-
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Mapping,
    Set,
    Type,
    Union,
)

from jinja2 import Template

from kiara.models.module.pipeline.pipeline import Pipeline
from kiara.renderers import RenderInputsSchema, SourceTransformer
from kiara.renderers.included_renderers.pipeline import PipelineTransformer
from kiara.renderers.jinja import BaseJinjaRenderer, JinjaEnv
from kiara.utils import log_message
from kiara_plugin.streamlit.components.input import (
    InputComponent,
)
from kiara_plugin.streamlit.streamlit import KiaraStreamlit

if TYPE_CHECKING:
    from kiara.context import Kiara


class PipelineRendererStreamlit(BaseJinjaRenderer[Pipeline, RenderInputsSchema]):
    """Renders a basic streamlit app from a pipeline structure."""

    _renderer_name = "pipeline_streamlit_app"

    def retrieve_jinja_env(self) -> JinjaEnv:

        jinja_env = JinjaEnv(template_base="kiara_plugin.streamlit")
        return jinja_env

    def retrieve_supported_render_sources(self) -> str:
        return "pipeline"

    def retrieve_supported_render_targets(cls) -> Union[Iterable[str], str]:
        return "streamlit_app"

    def retrieve_source_transformers(self) -> Iterable[SourceTransformer]:
        return [PipelineTransformer(kiara=self._kiara)]

    def get_template(self, render_config: RenderInputsSchema) -> Template:

        return self.get_jinja_env().get_template("pipeline/streamlit_app.py.j2")

    def assemble_render_inputs(
        self, instance: Any, render_config: RenderInputsSchema
    ) -> Mapping[str, Any]:

        inputs: Dict[str, Any] = render_config.model_dump()
        inputs["pipeline"] = instance
        return inputs

    def _post_process(self, rendered: str) -> str:

        try:
            import black
            from black import Mode  # type: ignore

            cleaned: str = black.format_str(rendered, mode=Mode())
            return cleaned

        except Exception as e:
            log_message(
                f"Could not format python code, 'black' not in virtual environment: {e}."
            )
            return rendered


class KiaraStreamlitTransformer(SourceTransformer):
    def __init__(self, kiara: "Kiara"):
        self._kiara: "Kiara" = kiara
        super().__init__()

    def retrieve_supported_python_classes(self) -> Iterable[Type]:
        return [str]

    def retrieve_supported_inputs_descs(self) -> Union[str, Iterable[str]]:
        return []

    def validate_and_transform(self, source: Any) -> Union[KiaraStreamlit, None]:

        if not source or source == "kiara_streamlit":
            context_config = self._kiara.context_config
            runtime_config = self._kiara.runtime_config
            return KiaraStreamlit(
                context_config=context_config, runtime_config=runtime_config
            )
        else:
            return None


class KiaraStreamlitAPIClassRenderer(
    BaseJinjaRenderer[KiaraStreamlit, RenderInputsSchema]
):
    """Renders a Python module containing a Protocol Class.

    This is useful for development, so all the dynamic components can be picked up by IDEs.
    """

    _renderer_name = "streamlit_api_class"

    def retrieve_jinja_env(self) -> JinjaEnv:

        jinja_env = JinjaEnv(template_base="kiara_plugin.streamlit")
        return jinja_env

    def retrieve_supported_render_sources(self) -> str:
        return "kiara_streamlit"

    def retrieve_supported_render_targets(cls) -> Union[Iterable[str], str]:
        return "python_code"

    def retrieve_source_transformers(self) -> Iterable[SourceTransformer]:
        return [KiaraStreamlitTransformer(kiara=self._kiara)]

    def get_template(self, render_config: RenderInputsSchema) -> Template:

        return self.get_jinja_env().get_template("code_gen/kiara_streamlit_api.py.j2")

    def assemble_render_inputs(
        self, instance: Any, render_config: RenderInputsSchema
    ) -> Mapping[str, Any]:

        render_config.model_dump()

        kiara_streamlit: KiaraStreamlit = instance
        components = kiara_streamlit.components

        all_methods = {}
        imports: Dict[str, Set] = {
            "typing": set(),
            "streamlit": set(),
            "kiara": set(),
            "uuid": set(),
        }
        # imports["kiara_plugin.streamlit.streamlit"] = {"KiaraStreamlit"}

        for comp_name in sorted(components.keys()):
            comp = components[comp_name]

            comp_info = comp.info
            doc = comp_info.documentation

            is_type_specific_select_comp = (
                isinstance(comp, InputComponent)
                and comp.component_name != "select_value"
            )

            params = []
            for arg_name, arg in comp_info.arguments.items():

                # better hide this component, otherwise it might be confusing
                if is_type_specific_select_comp and arg_name in [
                    "value_schema",
                    "data_type",
                ]:
                    continue

                if isinstance(arg.default, str):
                    arg_default = f'"{arg.default}"'
                else:
                    arg_default = arg.default

                arg_type = arg.python_type
                arg_type_string = arg.python_type_string

                module = arg_type.__module__
                if module != "builtins":
                    imports.setdefault(module, set()).add(arg_type.__name__)

                # sorry, this is dodgy as...
                if arg_default is not None:
                    params.append(
                        {
                            "name": arg_name,
                            "type": arg_type_string,
                            "default": arg_default,
                        }
                    )
                elif "Union" in arg_type_string and "None" in arg_type_string:
                    params.append(
                        {
                            "name": arg_name,
                            "type": arg_type_string,
                            "default": arg_default,
                        }
                    )
                else:
                    params.append({"name": arg_name, "type": arg_type_string})

            imports["typing"] = set()
            signature = ["self"]
            for param in params:
                if "default" in param.keys():
                    continue
                token = f"{param['name']}: \"{param['type']}\""
                signature.append(token)

            for param in params:
                if "default" not in param.keys():
                    continue
                token = f"{param['name']}: \"{param['type']}\""
                token += f" = {param['default']}"
                signature.append(token)

            signature_string = f"def {comp_name}({', '.join(signature)})"
            signature_string = signature_string.replace("NoneType", "None")
            signature_string = signature_string.replace("Literal", "str")
            all_methods[signature_string] = doc

        data = {"imports": imports, "methods": all_methods}

        return data

    def _post_process(self, rendered: str) -> str:

        try:
            import black
            from black import Mode  # type: ignore

            cleaned: str = black.format_str(rendered, mode=Mode())
            return cleaned

        except Exception as e:
            log_message(
                f"Could not format python code, 'black' not in virtual environment: {e}."
            )
            return rendered
