# -*- coding: utf-8 -*-

from streamlit.delta_generator import (
    Block_pb2,
    DeltaGenerator,
    ForwardMsg_pb2,
    _enqueue_message,
    caching,
    current_form_id,
    cursor,
)
from streamlit.elements.form import FormData

# copied from: https://github.com/joy13975/streamlit-nested-layout/blob/main/streamlit_nested_layout/nest.py
# License: Apache License 2.0
# Copyright Joy Yeh


def _nestable_block(
    self,
    block_proto: Block_pb2.Block = Block_pb2.Block(),  # type: ignore
) -> "DeltaGenerator":
    # Operate on the active DeltaGenerator, in case we're in a `with` block.
    dg: "DeltaGenerator" = self._active_dg

    # Prevent nested columns & expanders by checking all parents.
    block_type = block_proto.WhichOneof("type")
    # Convert the generator to a list, so we can use it multiple times.
    # parent_block_types = frozenset(dg._parent_block_types)
    # if block_type == "column" and block_type in parent_block_types:
    #     raise StreamlitAPIException(
    #         "Columns may not be nested inside other columns."
    #     )
    # if block_type == "expandable" and block_type in parent_block_types:
    #     raise StreamlitAPIException(
    #         "Expanders may not be nested inside other expanders."
    #     )

    if dg._root_container is None or dg._cursor is None:
        return dg

    msg = ForwardMsg_pb2.ForwardMsg()  # type: ignore
    msg.metadata.delta_path[:] = dg._cursor.delta_path
    msg.delta.add_block.CopyFrom(block_proto)

    # Normally we'd return a new DeltaGenerator that uses the locked cursor
    # below. But in this case we want to return a DeltaGenerator that uses
    # a brand new cursor for this new block we're creating.
    block_cursor: cursor.RunningCursor = cursor.RunningCursor(  # type: ignore
        root_container=dg._root_container,  # type: ignore
        parent_path=dg._cursor.parent_path + (dg._cursor.index,),  # type: ignore  # noqa
    )
    block_dg = DeltaGenerator(
        root_container=dg._root_container,
        cursor=block_cursor,
        parent=dg,
        block_type=block_type,
    )
    # Blocks inherit their parent form ids.
    # NOTE: Container form ids aren't set in proto.
    block_dg._form_data = FormData(current_form_id(dg))

    # Must be called to increment this cursor's index.
    dg._cursor.get_locked_cursor(last_index=None)
    _enqueue_message(msg)

    caching.save_block_message(  # type: ignore
        block_proto,
        invoked_dg_id=self.id,
        used_dg_id=dg.id,
        returned_dg_id=block_dg.id,
    )

    return block_dg


DeltaGenerator._block = _nestable_block  # type: ignore
