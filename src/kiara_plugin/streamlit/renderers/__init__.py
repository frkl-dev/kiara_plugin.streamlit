# -*- coding: utf-8 -*-
from typing import Any, Iterable, Mapping, Union

from jinja2 import Template
from kiara.models.module.pipeline.pipeline import Pipeline
from kiara.renderers import RenderInputsSchema, SourceTransformer
from kiara.renderers.included_renderers.pipeline import PipelineTransformer
from kiara.renderers.jinja import BaseJinjaRenderer, JinjaEnv
from kiara.utils import log_message


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
