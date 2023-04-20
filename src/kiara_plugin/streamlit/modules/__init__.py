# -*- coding: utf-8 -*-
from typing import Any, Dict, Mapping

from boltons.strutils import slugify
from pydantic import Field

from kiara.api import KiaraModule, KiaraModuleConfig, ValueMap, ValueMapSchema
from kiara.models.module.pipeline import PipelineConfig


class DummyModuleConfig(KiaraModuleConfig):
    @classmethod
    def create_pipeline_config(
        cls, title: str, description: str, author: str, *steps: "DummyModuleConfig"
    ) -> PipelineConfig:

        data: Dict[str, Any] = {
            "pipeline_name": slugify(title),
            "doc": description,
            "context": {"authors": [author]},
            "steps": [],
        }
        for step in steps:
            step_data = {
                "step_id": slugify(step.title),
                "module_type": "dummy",
                "module_config": {
                    "title": step.title,
                    "inputs_schema": step.inputs_schema,
                    "outputs_schema": step.outputs_schema,
                    "desc": step.desc,
                },
            }
            data["steps"].append(step_data)

        pipeline_config = PipelineConfig.from_config(data)
        return pipeline_config

    inputs_schema: Dict[str, Dict[str, Any]] = Field(
        description="The input fields and their types.",
    )

    outputs_schema: Dict[str, Dict[str, Any]] = Field(
        description="The outputs fields and their types.",
    )
    title: str = Field(description="The title of the step.")

    desc: str = Field(description="A description of what this step does.")


class Dummymodule(KiaraModule):

    _module_type_name = "dummy"
    _config_cls = DummyModuleConfig

    def create_inputs_schema(
        self,
    ) -> ValueMapSchema:

        result = {}
        v: Mapping[str, Any]
        for k, v in self.get_config_value("inputs_schema").items():
            data = {
                "type": v["type"],
                "doc": v.get("doc", "-- n/a --"),
                "optional": v.get("optional", True),
            }
            result[k] = data

        return result

    def create_outputs_schema(
        self,
    ) -> ValueMapSchema:

        result = {}
        for k, v in self.get_config_value("outputs_schema").items():
            data = {
                "type": v["type"],
                "doc": v.get("doc", "-- n/a --"),
                "optional": v.get("optional", False),
            }
            result[k] = data

        return result

    def process(self, inputs: ValueMap, outputs: ValueMap) -> None:

        config = self.get_config_value("desc")
        print(f"XXXX: {config}")

        outputs_schema = self.get_config_value("outputs_schema")
        field_name = next(iter(outputs_schema.keys()))
        outputs.set_value(field_name, "result")
