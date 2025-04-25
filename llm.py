from openai import OpenAI

API_KEY = 'sk-44a071209dad4d2fb2e21827c773e02e'

def generate_prompt():
    prompt = ""
    return prompt

def call_llm(prompt):
    client = OpenAI(
        api_key=API_KEY, 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云API端点
    )

    response = client.chat.completions.create(
        model="qwen-max-2025-01-25",  # 模型名称
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def retry_call_llm(marker, candidates, max_retries=3):
    for attempt in range(max_retries):
        prompt = generate_prompt()
        print(prompt)
        llm_output = call_llm(prompt)
        print(llm_output)
        corrected_marker, reason = process_llm_output(llm_output)

        if corrected_marker != "UNKNOWN":
            return corrected_marker, reason
        print(f"第 {attempt+1} 次尝试修正 `{marker}` 失败，返回 UNKNOWN，重新请求 LLM...")

    return "UNKNOWN", "UNKNOWN"  # 3 次都失败则返回 UNKNOWN


def process_llm_output(llm_output):
    pass