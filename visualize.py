from openai import OpenAI
import base64
import requests
import google.generativeai as genai
from io import BytesIO
from PIL import Image
import os


def generate_response(api_key, demand, num_of_columns, columns_name, columns_type, full_file_url):
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    # read uploaded file from full_file_url
    response = requests.get(full_file_url)
    if response.status_code == 200:
        uploaded_file = response.content
    if uploaded_file:
        # Get uploaded_file's name
        file_name = full_file_url.split('/')[-1]

        first_prompt = f"\"\"\"\nDùng tập dữ liệu gọi là df từ {file_name}. Đây là đường dẫn đến file: {full_file_url}\n\"\"\""
        second_prompt = ""
        for i in range(num_of_columns):
            if columns_type[i][0] == 'Categorical':
                second_prompt += f"Cột {columns_name[i]} có kiểu phân loại. Với các giá trị là {columns_type[i][1]}.\n"
            elif columns_type[i][0] == 'Numeric':
                second_prompt += f"Cột {columns_name[i]} Có kiểu số. Với kiểu số là {columns_type[i][1]}.\n"
            elif columns_type[i][0] == 'Date':
                second_prompt += f"Cột {columns_name[i]} có kiểu thời gian (ngày tháng).\n"
            elif columns_type[i][0] == 'Boolean':
                second_prompt += f"Cột {columns_name[i]} có kiểu boolean.\n"
        
        third_prompt = "Dán nhãn các trục một cách thích hợp với biểu đồ. Thêm tiêu đề dùng tiếng Việt và để trống phụ đề của subplot trong fig, thêm legend nếu cần thiết."
        forth_prompt = f"Dùng phiên bản Python 3.11, tạo 1 script duy nhất dùng dữ liệu df để trực quan yêu cầu sau: {demand}."

        description_prompt = f"{first_prompt}\n{second_prompt}\n{third_prompt}\n{forth_prompt}\n"
        code_prompt = '''
        import pandas as pd
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(10, 4))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        df = input_df.copy()"""'''
        
        prompt = f"{description_prompt}\n{code_prompt}"

        messages = [
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = client.chat.completions.create(
            model="llama-3-sonar-large-32k-online",
            messages=messages,
            temperature=0,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    return None


### GEMINI

def upload_to_gemini(path_or_url, mime_type=None):
    """Uploads the given file or image from URL to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        response = requests.get(path_or_url)
        if response.status_code == 200:
            # Save the image to a temporary file
            img = Image.open(BytesIO(response.content))
            temp_path = 'temp_image.' + img.format.lower()
            img.save(temp_path)
            file = genai.upload_file(temp_path, mime_type=mime_type)
            os.remove(temp_path)  # Clean up temporary file
        else:
            raise ValueError("Failed to download image from URL.")
    else:
        file = genai.upload_file(path_or_url, mime_type=mime_type)
    
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def generate_img_comment(gemini_key, demand, img_url):
    """
    Generates a comment for an image using the Gemini AI API.
    """

    genai.configure(api_key=gemini_key)

    # Create the model
    # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
    generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 300,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
    )

    # TODO Make these files available on the local file system
    # You may need to update the file paths
    files = [
    # upload_to_gemini("uploads\images\plot.png", mime_type="image/png"),
    upload_to_gemini(img_url, mime_type="image/png"),
    ]

    chat_session = model.start_chat(
        history=[
            {"role": "user",
             "parts": [files[0]]
            },
        ]
    )

    response = chat_session.send_message(f"Từ biểu đồ, rút ra kết luận và trả lời yêu cầu bằng tiếng Việt:: {demand}")

    return response.text