# -*- coding: utf-8 -*-
import abc
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from kiara_plugin.streamlit.api import KiaraStreamlitAPI


@runtime_checkable
class KiaraStreamlitModal(Protocol):
    @abc.abstractmethod
    def show_modal(self, st: "KiaraStreamlitAPI") -> bool:
        pass


class KiaraStreamlitModalCreate(object):
    def show_modal(self, st: "KiaraStreamlitAPI") -> bool:

        int_input = st.kiara.input_integer(label="Number of items")
        st.kiara.preview(int_input)

        finished = st.button("Finish")
        return finished
