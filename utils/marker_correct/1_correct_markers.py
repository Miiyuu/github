import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI
import os
import json
import argparse

API_KEY = 'sk-44a071209dad4d2fb2e21827c773e02e'

# hgnc_file = r"sources\hgnc_complete_set.txt"
# false_markers_file = r"output\exp_3\marker\false_markers.csv"
# greek_map_file = r'sources\greek_map.json'
# output_file = r"output/exp_3/marker/corrected_markers.csv"

# 1. 数据加载
def parse_args():
    parser = argparse.ArgumentParser(description='基因标记标准化工具')
    parser.add_argument('--hgnc_file', required=True, help='HGNC数据库文件路径')
    parser.add_argument('--false_markers_file', required=True, help='待修正标记文件路径')
    parser.add_argument('--greek_map_file', required=True, help='希腊字母映射文件路径')
    parser.add_argument('--output_file', required=True, help='输出文件路径')
    return parser.parse_args()

def load_data(hgnc_file, false_markers_file):
    # 加载HGNC数据库
    df_hgnc = pd.read_csv(hgnc_file, sep="\t", low_memory=False)
    df_hgnc['alias_symbol'] = df_hgnc['alias_symbol'].fillna("").apply(lambda x: x.split("|") if x else [])
    df_hgnc['prev_symbol'] = df_hgnc['prev_symbol'].fillna("").apply(lambda x: x.split("|") if x else [])
    
    # 加载待修正的标记
    try:
        false_markers = pd.read_csv(
            false_markers_file,
            encoding='utf-8'
        )['marker'].unique()
    except UnicodeDecodeError:
        false_markers = pd.read_csv(
            false_markers_file,
            encoding='latin1'
        )['marker'].unique()
    return df_hgnc, false_markers

# 2. 检索预处理
def build_search_index(df_hgnc):
    # 确保所有字段是列表（处理NaN或非列表类型）
    df_hgnc['alias_symbol'] = df_hgnc['alias_symbol'].apply(lambda x: x if isinstance(x, list) else [])
    df_hgnc['prev_symbol'] = df_hgnc['prev_symbol'].apply(lambda x: x if isinstance(x, list) else [])
    df_hgnc['alias_name'] = df_hgnc['alias_name'].apply(lambda x: x if isinstance(x, list) else [])
    df_hgnc['prev_name'] = df_hgnc['prev_name'].apply(lambda x: x if isinstance(x, list) else [])

     # 定义清理文本的函数
    def clean_text(text):
        # 移除括号、逗号等特殊字符，替换为空格
        text = re.sub(r'[(),"|]', ' ', str(text))
        # 合并多个空格为单个空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # 合并搜索字段（清理每个字段）
    df_hgnc['search_text'] = df_hgnc.apply(
        lambda x: ' '.join(filter(None, [
            clean_text(x['symbol']),
            clean_text(' '.join(x['alias_symbol'])),
            clean_text(' '.join(x['prev_symbol'])),
            clean_text(x['name']),
            clean_text(' '.join(x['alias_name'])),
            clean_text(' '.join(x['prev_name']))
        ])).lower(),  # 统一转为小写
        axis=1
    )

    print(df_hgnc['search_text'][0])
    print(df_hgnc['search_text'][1])
    print(df_hgnc['search_text'][2])
    
    # 构建TF-IDF索引
    # vectorizer = TfidfVectorizer()
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),  # 同时考虑单词和双词（如 "t brachyury"）
        max_df=0.8,
        token_pattern=r'(?u)\b\w+\b|\b\w+\s\w+\b'
    )
    # tfidf_matrix = vectorizer.fit_transform(df_hgnc['search_text'])
    tfidf_matrix = vectorizer.fit_transform(df_hgnc['search_text'].apply(lambda x: x.lower())) # 不区分大小写
    return vectorizer, tfidf_matrix

# 4. 检索候选
def retrieve_candidates(query, df_hgnc, vectorizer, tfidf_matrix, top_k=5):
    query_vec = vectorizer.transform([query])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = sim_scores.argsort()[-top_k:][::-1]

    # 获取对应的行数据
    top_matches = df_hgnc.iloc[top_indices]
    
    # 提取所需字段并格式化为字典列表
    results = []
    for _, row in top_matches.iterrows():
        result = {
            'symbol': str(row['symbol']),
            'alias_symbol': ' '.join(row['alias_symbol']) if isinstance(row['alias_symbol'], (list, tuple)) else str(row['alias_symbol']),
            'prev_symbol': ' '.join(row['prev_symbol']) if isinstance(row['prev_symbol'], (list, tuple)) else str(row['prev_symbol']),
            'name': str(row['name']),
            'alias_name': ' '.join(row['alias_name']) if isinstance(row['alias_name'], (list, tuple)) else str(row['alias_name']),
            'prev_name': ' '.join(row['prev_name']) if isinstance(row['prev_name'], (list, tuple)) else str(row['prev_name'])
        }
        results.append(result)
    
    return results

    # return df_hgnc.iloc[top_indices].to_dict('records')

# 5. Prompt生成与大模型调用
def generate_prompt(marker, candidates):
    # prompt = f"""
    # 你是一个基因标记标准化工具，需要根据 HGNC 数据库修正以下标记。请遵循规则：
    # 1. 优先选择 HGNC 的 `symbol` 作为标准化结果。
    # 2. 处理希腊字母、别名、格式冗余等问题，确保输出的是标准化基因符号。
    # 3. 如果无法匹配合适的标准基因符号，直接输出 `UNKNOWN`，但格式必须与以下示例保持一致。

    # 请严格按照如下格式输出：
    # ```
    # 修正结果: <标准化的基因符号>
    # ```

    # 现在请处理以下标记：
    # 原始标记: "{marker}"
    # 候选信息: {candidates}
    # """

    prompt = f"""
    你是一个基因标记标准化工具，需要根据候选信息修正原始标记，将其名称修正为候选信息中的标准化结果。你会得到一个候选信息列表，其中包括5个检索出的候选信息，它们的排序是随机打乱的。请在所有候选信息中，选择你认为跟marker最匹配的结果。如果能够找到，就选择候选信息中的'symbol'作为标准化结果；如果找不到，就返回原始标记名称。给出你的理由。
    请严格按照如下格式输出：
    ```
    理由: <理由>
    修正结果: <标准化的基因符号>
    ```
    
    现在请处理以下标记：
    原始标记: "{marker}"
    候选信息列表: {candidates}
    """
    return prompt

import re

def process_llm_output(llm_output):
    """
    从大模型的输出中提取修正后的基因符号和理由。
    返回格式: (修正结果, 理由)
    """
    # 匹配 "理由: <理由内容>" 和 "修正结果: <基因符号>"
    pattern = r"理由:\s*(.*?)\n修正结果:\s*(\S+)"
    match = re.search(pattern, llm_output, re.DOTALL)  # re.DOTALL 确保匹配多行理由
    
    if match:
        reason = match.group(1).strip()  # 提取理由并去除首尾空格
        corrected_symbol = match.group(2).strip()  # 提取修正结果
        return corrected_symbol, reason
    else:
        print("无法解析输出，原始输出:", llm_output)
        return None, None  # 或返回 ("UNKNOWN", "未找到匹配")

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

def retry_call_llm(marker, candidates, api_key, max_retries=3):
    for attempt in range(max_retries):
        prompt = generate_prompt(marker, candidates)
        print(prompt)
        llm_output = call_llm(prompt)
        print(llm_output)
        corrected_marker, reason = process_llm_output(llm_output)

        if corrected_marker != "UNKNOWN":
            return corrected_marker, reason
        print(f"第 {attempt+1} 次尝试修正 `{marker}` 失败，返回 UNKNOWN，重新请求 LLM...")

    return "UNKNOWN", "UNKNOWN"  # 3 次都失败则返回 UNKNOWN

def pre_process(false_markers, greek_map_file):
    # 处理长标记 list，拆分为多个标记进行修正
    expanded_markers = []
    # 第一轮处理：去掉括号前的空格
    for i, marker in enumerate(false_markers):
        # 检查是否有括号，并且括号前有空格
        if '(' in marker and ' ' in marker.split('(')[0]:
            false_markers[i] = re.sub(r'\s+(?=\()', '', marker)  # 去掉括号前的空格
            # print(false_markers[i])
    
    # 第二轮处理：拆分标记
    for marker in false_markers:
        # 按照空格拆分成多个标记
        split_markers = marker.split()  # 按空格拆分
        expanded_markers.extend([m.strip() for m in split_markers if m.strip()])

    # return expanded_markers
    
    # 第三轮：处理希腊字母
    with open(greek_map_file, 'r', encoding='utf-8') as file:
        greek_map = json.load(file)

    converted_list = []
    for s in expanded_markers:
        converted_str = []
        for char in s:
            if char in greek_map:
                converted_str.append(greek_map[char].lower()) # 转小写
            else:
                converted_str.append(char)
        converted_list.append(''.join(converted_str))
    
    # # 第四步：去除冗余符号 --> 是否有必要？
    # converted_list = [re.sub(r"[()+-]", " ", s) for s in converted_list]
    converted_list = [re.sub(r"[()]", " ", s) for s in converted_list]
    converted_list = [re.sub(r"\b(gene|protein)\b", "", s) for s in converted_list]

    return converted_list

def main():
    args = parse_args()
    
    # 加载数据
    df_hgnc, false_markers = load_data(args.hgnc_file, args.false_markers_file)
    false_markers = pre_process(false_markers, args.greek_map_file)

    # 构建搜索索引
    vectorizer, tfidf_matrix = build_search_index(df_hgnc)

    # 初始化结果列表
    results = []
    
    # 处理每个标记
    for i, marker in enumerate(false_markers, 1):
        candidates = retrieve_candidates(marker, df_hgnc, vectorizer, tfidf_matrix)
        corrected_marker, reason = retry_call_llm(marker, candidates, API_KEY)
        
        current_result = {
            "original": marker,
            "corrected": corrected_marker,
            "candidates": candidates,
            "reason": reason
        }
        results.append(current_result)
        
        if i == 1:
            pd.DataFrame([current_result]).to_csv(args.output_file, index=False)
        else:
            pd.DataFrame([current_result]).to_csv(args.output_file, mode='a', header=False, index=False)
    
    print("\nAll markers processed. Results saved to:", args.output_file)

if __name__ == "__main__":
    main()