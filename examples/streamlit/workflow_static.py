# -*- coding: utf-8 -*-
import os

import nltk

import kiara_plugin.streamlit as kst
from kiara.interfaces.python_api import OperationInfo
from kiara_plugin.streamlit.components.workflow.static import WorkflowSessionStatic

st = kst.init(page_config={"layout": "wide"})

nltk.download("punkt")
nltk.download("stopwords")

EXPLANATION = """
This is an example of how to render a pre-assembled pipeline as a workflow UI. All of this is rendered auto-matically, using the content of this pipeline:

- https://github.com/DHARPA-Project/kiara_plugin.streamlit/blob/develop/examples/streamlit/pipelines/topic_modeling.yaml

The whole experience is a bit clunky, which is par for the course for a fully-auto-rendered, interactive multi-page form like this. It'll be possible to augment the pipeline description I linked above with additional hints, which will improve the UI experience substantially (e.g. only present column names available in the selected table, instead of asking the user to input the column names free-form).

As it is, I think this is still a good enough demo to show which UI components are generally necessary for users to make informed decisions, esp. the input/output previews are very important IMHO. Overall, I imagine something like this (in terms of functionality) to be a main part of the first version of our UI (also: a data-set management component, and data onboarding helpers). I think we'll rely on pre-assembled workflows/pipeline (done by us ourselves), dynamic, data-centric workflows and pipeline creation by users is not a priority for the first version.

To try out this demo, there are a few inputs that are non obvious for now (for the reasons explained above), so here is a quick rundown what is happening:

- General:
   - a final UI would have also descriptions of what happens in every step/stage, and links to documentation, etc.
   - the pipeline does some topic modeling on a text corpus
   - a stage consists of one or several steps, grouped depending on when the first time is a user input is required for each step
   - click process after you changed inputs, so the workflow can process intermediate outputs for each stage
   - click 'Next step' after the process, to progress to the next stage

- Stage 1

   - Select the corpus (only 1 available for this demo, for now) -- this is basically just a folder with text files
   - languages and stopword lists are not supported yet, so just leave them as they are

- Stage 2

   - this needs to know the names of the column where the required data is, you can look that up in the 'Outputs (previous stages)' expander, or just use: 'content' for `extract_texts_column__column_name`. A 'production' UI would give the user a combobox or similar with only the available column names here...

- Stage 3

   - this stage tokenizes the text content and also creates a list of stop words that will be used later in the pre-processing step. Just keep the `tokenize_by_word` input checked (unchecked would make sense for some asian languages), and maybe add 'italian' to the `languages` input. To test, you can also add some stopwords manually here.

- Stage 4

   - this stage pre-processes the tokens we computed in the previous stage, removes stopwords, etc. You can't do anything wrong. Just play a bit with the options and see how the result changes

- Stage 5

   - the final step, if you know about topic modeling, then the results will make sense, otherwise, probably not. Select to create a few topics (maybe `num_topics_min` 5 and num_topics_max 9), check `compute_coherence` and words_per_topic 3. Our production app would have a lot more explanations and documentation what any of the inputs and outputs mean, what exactly happens, what LDA is, etc.
"""
with st.expander("Notes (click to hide)", expanded=True):
    st.markdown(EXPLANATION)


current = st.kiara.api.get_current_context_name()
with st.sidebar:
    selected_context = st.kiara.context_switch_control(allow_create=True, key="xxx")
    context_changed = current != selected_context


with st.spinner("Registering pipelines ..."):
    if "topic_modeling" not in st.kiara.api.list_operation_ids():
        pipelines_path = os.path.join(
            os.path.dirname(__file__), "pipelines", "topic_modeling.yaml"
        )
        ops = st.kiara.api.register_pipelines(pipelines_path)

pipeline = None
if "selected_pipeline" in st.session_state:
    pipeline = st.session_state["selected_pipeline"]

with st.sidebar:
    new_pipeline_info: OperationInfo = st.kiara.select_pipeline(
        filters=["topic_modeling"]
    )
    new_pipeline = new_pipeline_info.operation.operation_id
    st.session_state["selected_pipeline"] = new_pipeline

# new_pipeline = "/home/markus/projects/kiara/kiara.examples/examples/pipelines/topic_modeling/topic_modeling.yaml"
workflow_ref = "workflow_static"

if workflow_ref not in st.session_state or context_changed or pipeline != new_pipeline:
    workflow = st.kiara.api.create_workflow(initial_pipeline=new_pipeline)
    workflow_session: WorkflowSessionStatic = WorkflowSessionStatic(workflow=workflow)
    st.session_state[workflow_ref] = workflow_session

else:
    workflow_session = st.session_state[workflow_ref]

if "example_corpus" not in st.kiara.api.list_alias_names():
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

        result = st.kiara.api.run_job(
            operation="import.file_bundle",
            inputs={
                "source": "https://github.com/DHARPA-Project/kiara.examples/archive/refs/heads/main.zip",
                "sub_path": "kiara.examples-main/examples/data/language_processing/text_corpus/data",
            },
        )
        st.kiara.api.store_value(value=result["file_bundle"], alias="example_corpus")


st.kiara.workflow(workflow_session)
