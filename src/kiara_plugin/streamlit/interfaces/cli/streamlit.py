# -*- coding: utf-8 -*-
from typing import Iterable

import rich_click as click

from kiara.utils.cli import output_format_option, terminal_print_model

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


@click.group("streamlit")
@click.pass_context
def streamlit(ctx):
    """Kiara context related sub-commands."""


@streamlit.command("list-components")
@click.argument("filter", nargs=-1, required=False)
@click.option(
    "--full-doc",
    "-d",
    is_flag=True,
    help="Display the full doc for all operations (when using 'terminal' as format).",
)
@output_format_option()
@click.pass_context
def list_components(ctx, filter: Iterable[str], full_doc: bool, format: str):
    """List all available streamlit components."""

    from kiara_plugin.streamlit.components import ComponentsInfo
    from kiara_plugin.streamlit.streamlit import KiaraStreamlit

    kiara_streamlit = KiaraStreamlit()

    components = kiara_streamlit.components

    title = "Available components"
    if filter:
        title = "Filtered components"
        temp = {}
        for comp_name, comp in components.items():
            match = True
            for f in filter:
                if f.lower() not in comp_name.lower():
                    match = False
                    break
            if match:
                temp[comp_name] = comp
        components = temp

    infos = ComponentsInfo.create_from_instances(
        title=title, kiara=kiara_streamlit.api.context, instances=components
    )

    terminal_print_model(infos, format=format, in_panel=title, full_doc=full_doc)
