# -*- coding: utf-8 -*-
import kiara_plugin.streamlit as kst
from kiara_plugin.streamlit.components.workflow.dynamic import WorkflowSessionDynamic

st = kst.init(page_config={"layout": "wide"})


EXPLANATION = """
This is an example of how an exploratory data-science workflow could (not should!) look like in 'pure' UI (without code), usually you'd use notebook tech like Jupyter for that. Obviously there are limitations, but there is also some 'guidance' inbuilt (which those notebooks lack), because all the possible operations for the dataset you choose are pre-filtered for you. Also, it ships with the documentation about everything it can do, which is kinda nice.

An alternative to this would be a node-based approach, something like the blender node editor ( https://www.youtube.com/watch?v=moKFSMJwpmE ) or  https://gimelstudio.github.io/

The prototype is a bit terse at the moment, and I haven't had time to think about guiding users through all this, so it might be that your initial experience is a bit confusing. But I figured it is probably not be a bad idea to expose you to this, because that way you can register with yourself the typical kind of problems new users would have, and that we are out to solve. I haven't implemented anything 'onboarding' yet (that's another one of the topics I plan to address with prototypes like this), so this thing has 2 datasets automatically included: 2 csv files that can be used to generate a network graph .

If you use any of those (preferable the nodes one), you can convert it into a table and once you do that you'll have access to the 'table-related' operations, like 'cut-column', or an sql-query one, which are at lest semi-useful for playing around with.

As contrast, check out the pipeline auto-rendered UI example: https://kiara-static-workflow.streamlit.app/

This has better usability by default for novice users, but obviously that would only work for one specific, pre-assembled scenario/pipeline, and there would be no freedom for the user to 'explore' on their own.

Another thing I want to show in the future is the whole area of onboarding data into kiara, and making it usable and flexible enough to be useful. I think that's our biggest challenge, so I am still thinking about how to best do it.

An example workflow, to create network_data from an edges file would be:

- select `journal_edges_file` as the inital value -- this is the data we want to work with for this workflow
- select `create_table.from.file` as the first operation -- this will convert the edges file into a table (with typed columns etc.) -- check out the 'Show operation details' to get information about the operation you selected.
- check 'first_row_is_header', and click process
- this module only has one output, so we can just select that using 'Select for next step'. This means that this result-dataset will be used as input for the next step
- now the app will show you all available operations that take a 'table' as one of the inputs
- maybe pick 'query.table' to run some sql against it:
- set the query to `select * from data where weight > 1` and leave relation name to 'data'
- click process
- again, we only have one result, so we can just select that
- now the app will show you the same operations as with the last step, since both values were of type `table`
- select `assemble.network_data.from.tables` as the next operation
- click the 'Preview' box above to see the table you are working with as input, select the inputs accordingly: 'Source', 'Target' (we don't need the 'id_column_name' in this particular instance because we don't hava a separate nodes table)
- select the only result for the next step again, tihs is of type 'network_data'. We don't have many modules yet to work with 'network_data', but I hope you get the idea where this is going...
"""

with st.expander("Notes (click to hide)", expanded=True):
    st.markdown(EXPLANATION)

current = st.kiara.api.get_current_context_name()
with st.sidebar:
    selected_context = st.kiara.context_switch_control(allow_create=True, key="xxx")
    context_changed = current != selected_context

workflow_ref = "workflow_dynamic"
if workflow_ref not in st.session_state or context_changed:
    workflow = st.kiara.api.create_workflow()
    workflow_session: WorkflowSessionDynamic = WorkflowSessionDynamic(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session
else:
    workflow_session = st.session_state[workflow_ref]

if not st.kiara.api.list_alias_names():
    with st.spinner("Downloading example data ..."):

        result = st.kiara.api.run_job(
            operation="import.file",
            inputs={
                "source": "https://github.com/DHARPA-Project/kiara.examples/raw/main/examples/data/network_analysis/journals/JournalNodes1902.csv"
            },
        )
        st.kiara.api.store_value(value=result["file"], alias="journal_nodes_file")

        result = st.kiara.api.run_job(
            operation="import.file",
            inputs={
                "source": "https://github.com/DHARPA-Project/kiara.examples/raw/main/examples/data/network_analysis/journals/JournalEdges1902.csv"
            },
        )
        st.kiara.api.store_value(value=result["file"], alias="journal_edges_file")

st.kiara.workflow(workflow_session)
