# -*- coding: utf-8 -*-

from kiara.interfaces.python_api import JobDesc, KiaraAPI
from kiara_plugin.streamlit import kiara_streamlit_init

st = kiara_streamlit_init(page_config={"layout": "wide"})
api: KiaraAPI = st.kiara.api

network_data = st.kiara.select_network_data(add_import_widget=True)

if not network_data:
    st.stop()

operations = api.list_operations(input_types="network_data")

operation_id = st.selectbox("Select an operation", operations)
show_op_info = st.checkbox("Show operation info")

if show_op_info:
    st.kiara.operation_info(operation_id)

op = api.get_operation(operation_id)

network_data_field_name = None
for field, schema in op.inputs_schema.items():
    # this will be unreliable if we have 2 network_data inputs
    if schema.type == "network_data":
        network_data_field_name = field
        break

# since we filtered operations with the requirement that they need to have at least one input with type network_data,
# 'network_data_field_name' should not be None

op_inputs = st.kiara.operation_inputs(
    operation_id, constants={network_data_field_name: network_data}
)

job_desc = JobDesc(operation=operation_id, inputs=op_inputs)
result = st.kiara.run_job_panel(
    job_desc=job_desc, preview_result=True, add_save_option=True
)

# if not result:
#     st.write("No result")
# else:
#     st.kiara.value_map_preview(result)
