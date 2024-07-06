import streamlit as st
import visualize
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from PIL import Image
import requests

def extract_python_code(response):
    code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return None


st.write('# App')

st.write('## Create plot with natural language')

# create a text input that hides the input
openai_key = st.text_input('OpenAI key:', type='password', key='openai_key')

# create a text input to visualize
demand = st.text_input('Bạn muốn trực quan như thế nào?', key='demand_input')

with st.sidebar:

    # create a file uploader on the left side
    uploaded_file = st.file_uploader('Upload your file', type=['csv', 'xlsx'], key='file_uploader')

    # create a text input to describe the file
    num_of_columns = st.number_input('Number of columns:', min_value=1, max_value=30, key='num_of_columns')

    # Container for the columns inputs
    with st.container(height=300):
        columns_name = []
        columns_type = []

        for i in range(num_of_columns):
            columns_name.append(st.text_input(f'Column {i+1} name:', key=f'column_name_{i}'))
            col_type = st.selectbox(f'Column {i+1} type:', ['Categorical', 'Numeric', 'Date', 'Boolean'], key=f'column_type_{i}')
            
            if col_type == 'Categorical':
                temp = st.text_input(f'Categorical values for column {i+1} (comma-separated):', key=f'categorical_values_{i}')
                categorical_values = [x.strip() for x in temp.split(',')]
                columns_type.append([col_type, categorical_values])
            elif col_type == 'Numeric':
                numeric_type = st.selectbox(f'Type of numeric for column {i+1}:', ['int', 'float'], key=f'numeric_type_{i}')
                columns_type.append([col_type, numeric_type])
            elif col_type == 'Date':
                columns_type.append([col_type])
            elif col_type == 'Boolean':
                columns_type.append([col_type])

# create a button to submit the form
submit = st.button('Submit', key='submit_button')

FLASK_SERVER_URL = 'http://localhost:5001'

if submit:
    if uploaded_file is not None:
        files = {'file': uploaded_file}
        response = requests.post(f'{FLASK_SERVER_URL}/upload', files=files)
        if response.status_code == 200:
            file_url = response.json().get('file_url')
            full_file_url = f"{FLASK_SERVER_URL}{file_url}"
            # st.write(full_file_url)
            # Load the uploaded file into a dataframe
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(full_file_url)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(full_file_url)
            else:
                st.error("Định dạng file không phù hợp")
                st.stop()

            response = visualize.generate_response(openai_key, demand, uploaded_file, num_of_columns, columns_name, columns_type, full_file_url)
            # st.write(response)
            code = extract_python_code(response)
            if code:
                # st.code(code, language='python')
                # Execute the extracted code
                exec_globals = {'plt': plt, 'pd': pd, 'df': df}
                exec(code, exec_globals)
                # Show the plot
                st.pyplot(plt)
                
                # Save the plot to a temporary file
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)

                
                # Prepare the files for upload to Flask server
                files = {'file': ('plot.png', buffer, 'image/png')}
                
                # Send POST request to upload the image to Flask server
                upload_response = requests.post(f'{FLASK_SERVER_URL}/upload', files=files)

                if upload_response.status_code == 200:
                    img_url = upload_response.json().get('file_url')
                    full_img_url = f"{FLASK_SERVER_URL}{img_url}"
                    st.write(full_img_url)

                    insights = visualize.generate_img_comment(openai_key, demand, img_url)
                    st.write("## Nhận xét từ hình ảnh")
                    st.write(insights)

    else:
        st.write("Hãy nhập file dữ liệu")


    
