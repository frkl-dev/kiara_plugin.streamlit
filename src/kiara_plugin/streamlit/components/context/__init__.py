# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING, Any, Callable, ClassVar, List, Union

from pydantic import Field

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


class ContextSwitchOptions(ComponentOptions):

    allow_create: bool = Field(
        description="Allow the user to create a new context.", default=False
    )
    switch_to_selected: bool = Field(
        description="Immediately switch to the selected context.", default=True
    )


class ContextSwitch(KiaraComponent[ContextSwitchOptions]):
    """A component to switch between kiara contexts.

    A *kiara* context is used to separate different sets of data and configuration, and is
    useful to keep datasets and processing results organized.
    """

    _options = ContextSwitchOptions
    _component_name = "context_switch_control"

    _examples: ClassVar = [
        {
            "doc": "Show a context switch control.\n\nAllow the user to create a new context, and don't immediately switch to the selected context. You can compare the result of this component call with a call to `st.api.current_context_name`, to figure out whether the user wants to switch or not.",
            "args": {
                "switch_to_selected": False,
                "allow_create": True,
            },
        }
    ]

    def _render(self, st: "KiaraStreamlitAPI", options: ContextSwitchOptions) -> str:

        if not options.allow_create:
            context_names = self.api.list_context_names()
            if "default" in context_names:
                context_names.pop(context_names.index("default"))
                context_names.insert(0, "default")
            current = self.api.get_current_context_name()

            selected_context = self.write_selectbox(
                st=st,
                items=context_names,
                key=["kiara_context", "context_name"],
                options=options,
                default=current,
                label="Select context",
                help="Select the active context.",
            )
            if selected_context != current:
                self.api.set_active_context(selected_context)

            return selected_context

        else:

            selectbox_placeholder = st.empty()
            checkbox_key = options.create_key("kiara_context", "new_context_checkbox")

            text_field_key = options.create_key(
                "kiara_context", "context_name", "text_field"
            )

            if self.get_session_var(options, "kiara_context", "created", default=False):
                self.set_session_var(options, "kiara_context", "created", value=False)
                self._session_state[text_field_key] = ""
                self._session_state[checkbox_key] = False

            create_context_checkbox = st.checkbox(
                "Create new context", key=checkbox_key
            )
            submitted = False
            if create_context_checkbox:
                with st.form(key=options.create_key("context_select_form")):

                    new_context_name = st.text_input(
                        label="Context name", key=text_field_key, value=""
                    )
                    submitted = st.form_submit_button("Create")

            current = self.api.get_current_context_name()
            if submitted:
                print(f"CREATING CONTEXT: {new_context_name}")
                self.api.create_new_context(new_context_name, set_active=False)
                # self.set_session_var(options, "kiara_context", "context_name", value=new_context_name)
                self.set_session_var(options, "kiara_context", "created", value=True)
                force = new_context_name
            else:
                self.set_session_var(options, "kiara_context", "created", value=False)
                force = None

            context_names = self.api.list_context_names()

            if "default" in context_names:
                context_names.pop(context_names.index("default"))
                context_names.insert(0, "default")

            selected_context = self.write_selectbox(
                st=selectbox_placeholder,  # type: ignore
                items=context_names,
                options=options,
                key=["kiara_context", "select_context"],
                force=force,
                default=current,
                label="Select context",
                help="Select the active context.",
            )

            if selected_context != current and options.switch_to_selected:
                self.api.set_active_context(selected_context)

            return selected_context

    def write_selectbox(
        self,
        st: "KiaraStreamlitAPI",
        options: ContextSwitchOptions,
        key: List[str],
        items: List[str],
        force: Any = None,
        default: Any = None,
        label: Union[str, None] = None,
        help: Union[str, None] = None,
        format_func: Callable[[Any], Any] = str,
    ) -> str:

        value_state_key = options.get_session_key(*key)
        widget_key = options.create_key(*key, "selectbox")

        idx = 0
        if force is not None:
            self._session_state[widget_key] = force
            idx = 0
        elif widget_key not in self._session_state:
            if default:
                idx = items.index(default)
            else:
                idx = 0

        if not label:
            label = "Select value"

        def _set_current_value():
            self._session_state[value_state_key] = self._session_state[widget_key]

        result: Union[str, None] = st.selectbox(
            label=label,
            options=items,
            key=widget_key,
            index=idx,
            on_change=_set_current_value,
            help=help,
            format_func=format_func,
        )

        if result is None:
            raise Exception("Unexpected result from selectbox: None")

        return result
