# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Union

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.modules import DummyModuleConfig

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class StepRequirementsOptions(ComponentOptions):
    pass


class StepRequirement(KiaraComponent[StepRequirementsOptions]):
    """A component to gather step requirements from users"""

    _component_name = "step_requirements"
    _options = StepRequirementsOptions

    _examples = [{"doc": "A simple example", "args": {}}]

    def _render(
        self, st: "KiaraStreamlitAPI", options: StepRequirementsOptions
    ) -> Union[None, DummyModuleConfig]:

        st.write("INSIDE COMPONENT")

        _key = options.create_key("step_title")
        title = st.text_input("Step title", key=_key)
        _key = options.create_key("step_desc")
        desc = st.text_area("Step description", key=_key)

        _key = options.create_key("create_btn")
        inputs_schema = {
            "input_1": {
                "type": "any",
                "doc": "The first input",
                "optional": True,
            }
        }

        outputs_schema = {
            "input_1": {
                "type": "any",
                "doc": "The step output",
            }
        }

        try:
            config = DummyModuleConfig(
                title=title,
                inputs_schema=inputs_schema,
                outputs_schema=outputs_schema,
                desc=desc,
            )  # type: ignore
            return config
        except Exception:
            return None
