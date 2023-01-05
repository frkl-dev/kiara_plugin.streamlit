# -*- coding: utf-8 -*-

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


import rich_click as click

from kiara_plugin.streamlit import KiaraStreamlit


@click.group("streamlit")
@click.pass_context
def streamlit(ctx):
    """Kiara context related sub-commands."""


@streamlit.command("run")
@click.pass_context
def run(ctx):
    """Run a streamlit app."""

    print("RUNNING")


@streamlit.command("list-components")
@click.pass_context
def list_components(ctx):
    """List all available streamlit components."""

    kiara_streamlit = KiaraStreamlit()
    print(kiara_streamlit)
    # dbg(kiara_streamlit.components)
