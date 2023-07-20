# -*- coding: utf-8 -*-
import kiara_plugin.streamlit as kst
from kiara.api import KiaraAPI

# st.set_page_config(layout="wide")

# This example app introduces kiara, a data orchestration software. It will walk you through creating a simple streamilt application, and some basic but essential functions that can be built on in further notebooks.

# first, we initialize the kiara streamlit integration
# that way, we'll get access to the kiara api and some custom components
# via the 'st' object
# a list of components can be found here: https://kiara-doc-components.streamlit.app/

st = kst.init(page_config={"layout": "wide"})

# for convenience, and for IDS to help us autocomplete, we assign the kiara api to a variable
kiara: KiaraAPI = st.kiara.api

# in most cases, we need to pick an operation we want to use. You can query the kiara api for the availble ones like:
#
#  st.write(kiara.list_operation_ids())
#
# or, on the command-line:
#
# kiara operation list
#
# or, go https://kiara-doc-operations.streamlit.app/ and have a look there

"""---"""

# Downloading files

# Great, now we know the different kind of operations we can use with kiara. Let’s start by introducing some files to our application, using the 'import.file' function.  First we want to find out what this operation does, and just as importantly, what inputs it needs to work.

# We'll put the result in an expander, because it's a lot of text.

"""# Download file

*kiara* will download a csv file from a url you provide, it will execute the 'download.file' operation. For details about this operation, click on the expander below.
"""
with st.expander("Show operation info 'import.file'", expanded=False):
    st.write(st.kiara.operation_info("import.file"))

# So from this, we know that `import.file` will download a single file from a remote location for us to use in kiara.  We need to give the function at least a source (url) and, if we want, a file name. These are the inputs.  In return, we will get the file and metadata about the file as our outputs.
# Let’s give this a go using some kiara sample data.
# First we define our inputs, then use kiara.run_job with our chosen operation, `import.file`, and save this as our outputs.

# For the url, we can actually ask the user, but giving them a default value in case they don't have one at hand.

default_url = "https://raw.githubusercontent.com/DHARPA-Project/kiara.examples/main/examples/data/network_analysis/journals/JournalNodes1902.csv"
url = st.text_input("Please provide a url to download", value=default_url)

# we want the user to kick of the download process, so we need to have a button they can use
download_button = st.button("Download file")
if download_button:
    # after looking at the operation info, we know that we need to provide a url and a file name
    inputs = {"source": url, "file_name": url.split("/")[-1]}
    outputs = kiara.run_job("import.file", inputs=inputs)
    # we need to store the download result in the session state, otherwise it would be lost after a script rerun
    st.session_state["download_result"] = outputs

download_result = st.session_state.get("download_result", None)
if not download_result:
    st.write("No file downloaded yet. Stoping now...")
    st.stop()

# We can easily preview any value that is registered in kiara, or maps of values
# Again, we wrap this in an expander, to keep the page clean
with st.expander("Preview download result"):
    st.kiara.value_map_preview(dict(download_result), key="download_result")

"""---"""

# Great! We’ve successfully downloaded the file, and we can see there’s lots of information here.
# At the moment, we’re most interested in the file output. This contains the actual contents of the file that we have just downloaded.
# Let’s separate this out and store it in a separate variable for us to use.

downloaded_file = download_result["file"]

# New Formats: Creating and Converting
#
# What next? We could transform the downloaded file contents into a different format.  Let’s use the operation list earlier, and look for something that allows us to create something out of our new file.
#
# Our file was orginally in a CSV format, so let’s make a table using create.table.from.file.
# Just like when we used download.file, we can double check what this does, and what inputs and outputs this involves by looking up the operation documentation.
# This time, we’re also going to use a variable to store the operation in - this is especially handy if the operation has a long name, or if you want to use the same operation more than once without retyping it.

"""# Creating a table

For our purpose, we need to transform the downloaded file into a table data type, so we can do table-y things with it later. *kiara* has the operation 'create.table.from.file' for this purpose. For details, click the expander below.
"""

op_id = "create.table.from.file"
create_table_info = kiara.retrieve_operation_info(op_id)

with st.expander(f"Show operation info '{op_id}'", expanded=False):
    st.kiara.operation_info(op_id)

# As we can see from the operation info, in addition to the file input, we can also specify whether the files' first row is a header,
# or not. This is important since if it's a header, we want the table names to follow it's content, and if not, we also need to know.
# This is a simple as operation inputs go, so let's render an input widget so the user can tell us what to do (by default, without any input,
# kiara will try to auto-determine the header status).

is_header = st.kiara.input_boolean(label="Is the first row a header?", key="is_header")

# Great, we have all the information we need now.
# Let’s go again.
# First we define our inputs, the downloaded file we saved earlier.
# Then use kiara.run_job with our chosen operation, this time stored as op_id.
# Once this is saved as our outputs, we can print it out."""

create_table_btn = st.button("Create table")
if create_table_btn:
    inputs = {"file": downloaded_file, "first_row_is_header": is_header}
    outputs = kiara.run_job(op_id, inputs=inputs)
    st.session_state["create_table_result"] = outputs

create_table_result = st.session_state.get("create_table_result", None)
if not create_table_result:
    st.write("No table created yet. Stoping now...")
    st.stop()

with st.expander("Preview create table result", expanded=False):
    st.kiara.value_map_preview(dict(create_table_result), key="create_table")

# This has done exactly what we wanted, and shown the contents from the downloaded file as a table. But we are also interested in some general (mostly internal) information and metadata, this time for the new table we have just created, rather than the original file itself.
#
# Let’s have a look.

outputs_table = create_table_result["table"]

with st.expander("Preview metadata of created table", expanded=False):
    st.write(outputs_table.dict())

# Querying our Data
# So now we have downloaded our file and converted it into a table, we want to actually explore it.
# To do this, we can query the table using SQL and some functions already included in kiara.
# After taking another look at that operation list, we figured out we want to use the 'query.table' one.

"""# Query the table

Now that we have our table, we can do things like querying it via SQL.
"""

with st.expander("Show operation info 'query.table'", expanded=False):
    st.kiara.operation_info("query.table")

query = st.text_input(
    "Please provide a query", value="SELECT * from data where City like 'Berlin'"
)

query_table_btn = st.button("Query table", disabled=not query)
if query_table_btn:
    inputs = {"table": outputs_table, "query": query}
    outputs = kiara.run_job("query.table", inputs=inputs)
    st.session_state["query_table_result"] = outputs

query_table_result = st.session_state.get("query_table_result", None)
if not query_table_result:
    st.write("No table created yet. Stoping now...")
    st.stop()

with st.expander("Preview table query result", expanded=True):
    st.kiara.value_map_preview(dict(query_table_result), key="table_query")
