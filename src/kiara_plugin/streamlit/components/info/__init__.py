# -*- coding: utf-8 -*-
import abc
from typing import Generic, List, Mapping, Tuple, Type, TypeVar, Union

from kiara.interfaces.python_api.models.info import ItemInfo
from pydantic import Field
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components import ComponentOptions, KiaraComponent
from kiara_plugin.streamlit.utils.components import create_list_component


class InfoCompOptions(ComponentOptions):
    class Config:
        arbitrary_types_allowed = True

    columns: Union[
        Tuple[int, int], Tuple[DeltaGenerator, DeltaGenerator], None
    ] = Field(description="The column layout to use for the next step.", default=(1, 4))
    height: Union[int, None] = Field(
        description="The height of the list component.", default=None
    )
    items: Union[str, List[str], None] = Field(
        description="The item(s) to show info for."
    )


ITEM_TYPE = TypeVar("ITEM_TYPE", bound=ItemInfo)


class KiaraInfoComponent(KiaraComponent[InfoCompOptions], Generic[ITEM_TYPE]):

    _options = InfoCompOptions

    @classmethod
    @abc.abstractmethod
    def get_info_type(cls) -> Type[ITEM_TYPE]:
        pass

    def _render(
        self, st: DeltaGenerator, options: InfoCompOptions
    ) -> Union[ITEM_TYPE, None]:

        items = options.items
        if items is None:

            _items = self.get_all_item_infos()

            # method = f"get_{self.get_info_type()}s_info"
            # if not hasattr(self.api, method):
            #     method = f"retrieve_{self.get_info_type()}s_info"
            #     if not hasattr(self.api, method):
            #         raise Exception(f"No method '{method}' found on kiara api object.")
            #
            # _items = getattr(self.api, method)()
            selected = self.render_all_info(
                st=st,
                key=options.create_key("all_infos"),
                items=_items,
                options=options,
            )
            if selected:
                return selected
            else:
                return None

        elif isinstance(items, str):

            # ignoring columns
            # method = f"get_{self.get_info_type()}_info"
            # if not hasattr(self.api, method):
            #     method = f"retrieve_{self.get_info_type()}_info"
            #     if not hasattr(self.api, method):
            #         raise Exception(f"No method '{method}' found on kiara api object.")
            #
            # _item = getattr(self.api, method)(items)

            _item = self.get_info_item(items)

            self.render_info(
                st=st,
                key=options.create_key(f"info_{items}"),
                item=_item,
                options=options,
            )
            return _item
        else:
            raise NotImplementedError()

    @abc.abstractmethod
    def get_all_item_infos(self) -> Mapping[str, ITEM_TYPE]:
        pass

    @abc.abstractmethod
    def get_info_item(self, item_id: str) -> ITEM_TYPE:
        pass

    @abc.abstractmethod
    def render_info(
        self, st: DeltaGenerator, key: str, item: ITEM_TYPE, options: InfoCompOptions
    ):
        pass

    def render_all_info(  # type: ignore
        self,
        st: DeltaGenerator,
        key: str,
        items: Mapping[str, ITEM_TYPE],
        options: InfoCompOptions,
    ) -> Union[None, ITEM_TYPE]:

        if options.columns is None:
            left, right = st.columns((1, 4))
        elif isinstance(options.columns[0], int):
            left, right = st.columns(options.columns)
        else:
            left, right = options.columns

        info_type_name = self.__class__.get_info_type().__name__.lower()

        selected_op = create_list_component(
            st=left,
            title=info_type_name.capitalize(),
            items=list(items.keys()),
            key=f"{key}_{info_type_name}_list",
            height=options.height,
        )

        if selected_op:
            item = items[selected_op]

            self.render_info(
                st=right,
                key=f"{key}__{info_type_name}_{selected_op}",
                item=item,
                options=options,
            )
            return item
        else:
            return None
