# -*- coding: utf-8 -*-
from streamlit.delta_generator import DeltaGenerator

from kiara_plugin.streamlit.components.preview import PreviewComponent, PreviewOptions


class NetworkDataPreview(PreviewComponent):
    """Preview a value of type 'network data'.

    Currently, this displays a graph, as well as the nodes and edges tables. The graph is only a preview, and takes a while to render depending on the network data size, this will replaced at some point.
    """

    _component_name = "preview_network_data"

    @classmethod
    def get_data_type(cls) -> str:
        return "network_data"

    def render_preview(self, st: DeltaGenerator, options: PreviewOptions):

        import networkx as nx
        import streamlit.components.v1 as components
        from kiara_plugin.network_analysis.models import NetworkData
        from pyvis.network import Network

        _value = self.api.get_value(options.value)
        db: NetworkData = _value.data
        tab_names = ["graph"]
        tab_names.extend(db.table_names)
        tabs = st.tabs(tab_names)

        # graph
        with tabs[0]:

            graph_types = ["non-directed", "directed"]
            _key = options.create_key("graph_type", "select", "radio")
            graph_type = st.radio("Graph type", graph_types, key=_key)
            if graph_type == "non-directed":
                graph = db.as_networkx_graph(nx.Graph)
            else:
                graph = db.as_networkx_graph(nx.DiGraph)

            vis_graph = Network(
                height="400px", width="100%", bgcolor="#222222", font_color="white"
            )
            vis_graph.from_nx(graph)
            vis_graph.repulsion(
                node_distance=420,
                central_gravity=0.33,
                spring_length=110,
                spring_strength=0.10,
                damping=0.95,
            )

            html = vis_graph.generate_html()
            components.html(html, height=435)

        for idx, table_name in enumerate(db.table_names, start=1):
            # TODO: this is probably not ideal, as it always loads all tables because
            # of how tabs are implemented in streamlit
            # maybe there is an easy way to do this better, otherwise, maybe not use tabs
            table = db.get_table_as_pandas_df(table_name)
            tabs[idx].dataframe(table, use_container_width=True)
