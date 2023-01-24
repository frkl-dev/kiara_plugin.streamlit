# -*- coding: utf-8 -*-
from typing import Any, List, Mapping, Type

from jinja2 import Template
from kiara.models.module.pipeline.pipeline import Pipeline
from kiara.renderers import RenderInputsSchema
from kiara.renderers.jinja import BaseJinjaRenderer, JinjaEnv
from kiara.utils import log_message


class PipelineRendererStreamlit(BaseJinjaRenderer[Pipeline, RenderInputsSchema]):

    _renderer_name = "pipeline_streamlit_renderer"

    _render_profiles = {"streamlit_app": {}}  # type: ignore

    @classmethod
    def retrieve_supported_render_source(cls) -> str:
        return "pipeline"

    @classmethod
    def retrieve_supported_python_classes(cls) -> List[Type[Any]]:
        return [Pipeline]

    def retrieve_jinja_env(self) -> JinjaEnv:

        jinja_env = JinjaEnv(template_base="kiara_plugin.streamlit")
        return jinja_env

    def get_template(self, render_config: RenderInputsSchema) -> Template:

        return self.get_jinja_env().get_template("pipeline/streamlit_app.py.j2")

    def assemble_render_inputs(
        self, instance: Any, render_config: RenderInputsSchema
    ) -> Mapping[str, Any]:

        inputs = render_config.dict()
        inputs["pipeline"] = instance
        return inputs

    def _post_process(self, rendered: str) -> str:

        try:
            import black
            from black import Mode  # type: ignore

            cleaned = black.format_str(rendered, mode=Mode())
            return cleaned

        except Exception as e:
            log_message(
                f"Could not format python code, 'black' not in virtual environment: {e}."
            )
            return rendered
