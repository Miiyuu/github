import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
import os
from tqdm import tqdm
import numpy as np
import json
import re
from openai import OpenAI
import argparse

# 配置参数
K = 3  # 检索organ_tissue的top K数量
P = 5  # 每个organ_tissue下检索cell_ontology_class和free_annotation的top P数量
MAX_RETRIES = 3  # LLM最大重试次数
API_KEY = 'sk-44a071209dad4d2fb2e21827c773e02e'

def parse_args():
    parser = argparse.ArgumentParser(description='细胞组织标准化工具')
    parser.add_argument('--input_false_cells', required=True, help='待修正细胞文件路径')
    parser.add_argument('--ts_standard', required=True, help='标准数据集文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    return parser.parse_args()

def load_data(input_false_cells, ts_standard):
    """加载数据"""
    # 加载标准数据集
    ts_df = pd.read_csv(ts_standard)
    # 去除重复和空值
    ts_df = ts_df.drop_duplicates().dropna()
    
    # 加载需要修正的数据
    false_cells = pd.read_csv(input_false_cells)
    
    return ts_df, false_cells

def preprocess_text(text):
    """简单的文本预处理"""
    if not isinstance(text, str):
        return ""
    # 转换为小写，去除前后空格
    return text.lower().strip()

def build_tfidf_index(corpus):
    """构建TF-IDF索引"""
    vectorizer = TfidfVectorizer(
        preprocessor=preprocess_text,        
        lowercase=True,
        ngram_range=(1, 2),  
        max_df=0.8,
        token_pattern=r'(?u)\b\w+\b|\b\w+\s\w+\b')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf_matrix

def search_top_matches(query, corpus, vectorizer, tfidf_matrix, top_n=3):
    """使用TF-IDF检索最相似的top_n个结果"""
    if not query or not isinstance(query, str):
        return []
    
    query_vec = vectorizer.transform([preprocess_text(query)])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = np.argsort(similarities)[-top_n:][::-1]
    results = [(corpus.iloc[i], similarities[i]) for i in top_indices if similarities[i] > 0]
    return results

def get_cell_candidates(ts_standard, tissue, cell_query, top_p):
    """获取特定组织下的细胞类型候选"""
    # 筛选该组织下的所有细胞类型
    tissue_data = ts_standard[ts_standard['organ_tissue'] == tissue]
    if tissue_data.empty:
        return []
    
    # 构建细胞类型的TF-IDF索引（合并cell_ontology_class和free_annotation）
    cell_corpus = tissue_data['cell_ontology_class'] + " " + tissue_data['free_annotation']
    vectorizer, tfidf_matrix = build_tfidf_index(cell_corpus)
    
    # 检索最相似的细胞类型
    cell_results = search_top_matches(cell_query, tissue_data, vectorizer, tfidf_matrix, top_p)
    
    return cell_results

def generate_prompt(original_tissue, original_cell, candidate_matches):
    """生成组织细胞标准化的prompt"""
    # 构建候选列表的文本描述
    candidate_text = ""
    for i, (tissue, cells) in enumerate(candidate_matches.items()):
        candidate_text += f"\n候选组织 {i+1}: {tissue}\n"
        for j, (cell, score) in enumerate(cells):
            cell_ontology = cell['cell_ontology_class']
            free_annotation = cell['free_annotation']
            candidate_text += f"  候选细胞 {j+1}: cell_ontology_class='{cell_ontology}', free_annotation='{free_annotation}' (相似度: {score:.2f})\n"
    
    prompt = f"""
    你是一个生物医学专家，正在帮助标准化细胞和组织类型的标注。请根据以下原始数据和从标准文件中检索得到的候选匹配，给出最合适的修正结果。修正时，优先选择与原始数据最匹配的组织-细胞类型组合。如果原始细胞类型与候选匹配中的细胞类型是包含关系，或细胞之间有发育关系等，也认为其匹配。注意，如果细胞类型匹配的是free_annotation，需要用其对应的cell_ontology_class作为细胞修正的结果。如果你认为没有合适的匹配，则保持原始数据不变。

    原始数据:
    - 原始组织: {original_tissue}
    - 原始细胞类型: {original_cell}

    候选匹配:{candidate_text}

    请严格按照如下格式输出：
    ```
    理由: <你的判断理由>
    修正组织: <修正后的组织类型>
    修正细胞: <修正后的细胞类型>
    ```
    """
    return prompt

def process_llm_output(llm_output):
    """
    从大模型的输出中提取修正结果
    返回格式: (corrected_tissue, corrected_cell, reason)
    """
    # 匹配模式
    pattern = r"理由:\s*(.*?)\n修正组织:\s*(.*?)\n修正细胞:\s*(.*)"
    match = re.search(pattern, llm_output, re.DOTALL)
    
    if match:
        reason = match.group(1).strip()
        corrected_tissue = match.group(2).strip()
        corrected_cell = match.group(3).strip()
        return corrected_tissue, corrected_cell, reason
    else:
        print("无法解析LLM输出:", llm_output)
        return None, None, None

def call_llm(prompt):
    """调用大模型API"""
    try:
        print("prompt: ", prompt)
        client = OpenAI(
            api_key=API_KEY, 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云API端点
        )
        response = client.chat.completions.create(
            model="qwen-max-2025-01-25",
            messages=[
                {"role": "system", "content": "你是一个专业的生物医学研究人员，擅长细胞和组织类型分类。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"调用大模型出错: {e}")
        return None

def retry_llm_correction(original_tissue, original_cell, candidate_matches, max_retries=MAX_RETRIES):
    """带重试机制的LLM调用"""
    for attempt in range(max_retries):
        prompt = generate_prompt(original_tissue, original_cell, candidate_matches)
        llm_output = call_llm(prompt)
        
        if llm_output:
            corrected_tissue, corrected_cell, reason = process_llm_output(llm_output)
            if corrected_tissue and corrected_cell:
                return corrected_tissue, corrected_cell, reason
        
        print(f"第 {attempt+1} 次尝试修正 `{original_tissue}/{original_cell}` 失败，重试...")
    
    # 所有尝试都失败，返回原始数据
    return original_tissue, original_cell, "LLM调用失败，保持原始数据"

def determine_status(original_tissue, corrected_tissue, original_cell, corrected_cell):
    """确定状态标签"""
    if corrected_tissue == original_tissue and corrected_cell == original_cell:
        return "unfound"
    elif corrected_tissue != original_tissue and corrected_cell == original_cell:
        return "found_tissue"
    else:
        return "found"

def process_all_cells(ts_standard, false_cells, top_k, top_p, output_path):
    """处理所有需要修正的细胞"""
    # 首先构建组织级别的TF-IDF索引
    tissue_corpus = ts_standard['organ_tissue'].drop_duplicates()
    tissue_vectorizer, tissue_tfidf = build_tfidf_index(tissue_corpus)
    
    # 初始化结果列表
    results = []
    stats = {
        'total': 0,
        'found': 0,
        'found_tissue': 0,
        'unfound': 0
    }
    
    # 处理每一行数据
    for _, row in tqdm(false_cells.iterrows(), total=len(false_cells), desc="处理细胞数据"):
        original_tissue = row['ori_tissue']
        original_cell = row['ori_cell_type']
        
        stats['total'] += 1
        
        # 第一步：检索最相似的组织
        tissue_matches = search_top_matches(original_tissue, tissue_corpus, tissue_vectorizer, tissue_tfidf, top_k)
        print(tissue_matches)
        
        candidate_matches = {}
        for tissue, _ in tissue_matches:
            # 第二步：在每个候选组织下检索最相似的细胞类型
            cell_matches = get_cell_candidates(ts_standard, tissue, original_cell, top_p)
            if cell_matches:
                candidate_matches[tissue] = cell_matches
        
        # 如果没有找到任何候选，保持原样
        if not candidate_matches:
            result = {
                'ori_tissue': original_tissue,
                'ori_cell_type': original_cell,
                'prompt': "" ,
                'corrected_tissue': original_tissue,
                'corrected_cell': original_cell,
                'reason': "候选匹配为空",
                'status': 'unfound'
            }
            results.append(result)
            stats['unfound'] += 1
            # 实时写入文件
            pd.DataFrame([result]).to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
            continue
        
        # 第三步：询问大模型进行判断
        prompt = generate_prompt(original_tissue, original_cell, candidate_matches)
        corrected_tissue, corrected_cell, reason = retry_llm_correction(
            original_tissue, original_cell, candidate_matches
        )
        print(reason)
        
        # 确定状态
        status = determine_status(original_tissue, corrected_tissue, original_cell, corrected_cell)
        
        # 构建结果记录
        result = {
            'ori_tissue': original_tissue,
            'ori_cell_type': original_cell,
            'prompt': prompt,
            'corrected_tissue': corrected_tissue,
            'corrected_cell': corrected_cell,
            'reason': reason,
            'status': status
        }
        results.append(result)
        stats[status] += 1
        
        # 实时写入文件
        pd.DataFrame([result]).to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
    
    return pd.DataFrame(results), stats

def main():
    args = parse_args()
    
    # 加载数据
    ts_standard, false_cells = load_data(args.input_false_cells, args.ts_standard)
    
    # 如果输出文件已存在，先删除
    if os.path.exists(args.output):
        os.remove(args.output)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # 处理所有细胞
    corrected_df, stats = process_all_cells(ts_standard, false_cells, K, P, args.output)
    
    # 打印统计信息
    print("\n处理完成！统计信息:")
    print(f"总处理条数: {stats['total']}")
    print(f"完全修正条数(found): {stats['found']}")
    # print(f"仅组织修正条数(found_tissue): {stats['found_tissue']}")
    # print(f"未修正条数(unfound): {stats['unfound']}")
    # print(f"修正率: {(stats['found']+stats['found_tissue'])/stats['total']:.2%}")
    print(f"结果已保存到: {args.output}")

if __name__ == "__main__":
    main()