from openai import OpenAI

def generate_response(api_key, demand, uploaded_file, num_of_columns, columns_name, columns_type, full_file_url):
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    if uploaded_file:
        # Get uploaded_file's name
        file_name = uploaded_file.name

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


def generate_img_comment(api_key, demand, img_url):
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    prompt = f"Chỉ dựa dữ liệu lấy được từ bức ảnh, rút ra kết luận và trả lời câu hỏi bằng tiếng Việt: {demand}\n\nBức ảnh: {img_url}\n\n"

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