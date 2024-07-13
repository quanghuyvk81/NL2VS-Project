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
import os

def extract_python_code(response):
    code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return None

def file_selector(folder_path='./uploads/data'):
    if not os.path.exists(folder_path):
        return None
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox('Select a file', filenames)
    return os.path.join(folder_path, selected_filename).replace(os.sep, '/')

st.write('# App')

st.write('## Create plot with natural language')

# create a text input that hides the input
perplexity_key = st.text_input('Perplexity key:', type='password', key='Perplexity')
gemini_key = st.text_input('Gemini key:', type='password', key='gemini_key')
# create a text input to visualize
demand = st.text_input('Bạn muốn trực quan như thế nào?', key='demand_input')

FLASK_SERVER_URL = 'http://localhost:5001'

with st.sidebar:
    # create a file uploader on the left side
    uploaded_file = st.file_uploader('Upload your file', type=['csv', 'xlsx'], key='file_uploader')
    # upload the file to the Flask server
    if uploaded_file is not None:
        st.write('success')
        files = {'file': uploaded_file}
        response = requests.post(f'{FLASK_SERVER_URL}/upload', files=files)
        if response.status_code == 200:
            st.success("File uploaded successfully")

    file_path = file_selector()
st.write("### Dưới đây là file bạn đã chọn:")
if file_path:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            st.error("Định dạng file không phù hợp")
            st.stop()
        if df is not None:
            st.write(df)

# create a button to submit the form
submit = st.button('Submit', key='submit_button')

if submit:
    if file_path:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            st.error("Định dạng file không phù hợp")
            st.stop()

        num_of_columns = len(df.columns)
        columns_name = df.columns.tolist()
        columns_type = []
        
        for col in df.columns:
            if pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == object:
                unique_values = df[col].unique().tolist()
                columns_type.append(['Categorical', unique_values])
            elif pd.api.types.is_numeric_dtype(df[col]):
                numeric_type = 'int' if pd.api.types.is_integer_dtype(df[col]) else 'float'
                columns_type.append(['Numeric', numeric_type])
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                columns_type.append(['Date'])
            elif pd.api.types.is_bool_dtype(df[col]):
                columns_type.append(['Boolean'])

        full_file_url = f"{FLASK_SERVER_URL}{file_path[1:]}"
        response = visualize.generate_response(perplexity_key, demand, num_of_columns, columns_name, columns_type, full_file_url)
        code = extract_python_code(response)
        if code:
            exec_globals = {'plt': plt, 'pd': pd, 'df': df}
            exec(code, exec_globals)
            st.pyplot(plt)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)

            files = {'file': ('plot.png', buffer, 'image/png')}
            upload_response = requests.post(f'{FLASK_SERVER_URL}/upload', files=files)

            if upload_response.status_code == 200:
                img_url = upload_response.json().get('file_url')
                full_img_url = f"{FLASK_SERVER_URL}{img_url}"
                # st.write(full_img_url)

                insights = visualize.generate_img_comment(gemini_key, demand, full_img_url)
                st.write("## Nhận xét từ hình ảnh")
                st.write(insights)
