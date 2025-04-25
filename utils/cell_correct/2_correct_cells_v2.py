import pandas as pd
import os
from tqdm import tqdm
import re
from openai import OpenAI
import argparse
from typing import Dict,List,Tuple

# 配置参数
MAX_RETRIES = 3  # LLM最大重试次数
API_KEY = 'sk-44a071209dad4d2fb2e21827c773e02e'
# API_KEY = 'sk-58b57d4dfcb44c0e8db5a16ae9814a5c'

input_search_result = r'D:\0-workingspace\key-marker\memory\exp_100\search_result.csv'
output = r'D:\0-workingspace\key-marker\output\exp_100\cell\corrected_tissue_cell_emb.csv'

def parse_args():
    parser = argparse.ArgumentParser(description='细胞组织标准化工具(基于预检索结果)')
    parser.add_argument('--input_search_result', required=True, help='预检索结果文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    return parser.parse_args()

def parse_search_result(search_result: str) -> Dict[str, List[Tuple[Dict, float]]]:
    """解析search_result字段为候选匹配字典"""
    candidate_matches = {}
    entries = search_result.split('; ')
    
    for entry in entries:
        try:
            # 处理可能存在的引号和空格问题
            entry = entry.strip()
            if not entry:
                continue
                
            parts = [p.strip() for p in entry.split(', ')]
            if len(parts) < 3:
                continue
                
            # 提取各部分信息
            tissue = parts[0].split('=')[1] if '=' in parts[0] else ''
            cell_ontology = parts[1].split('=')[1] if '=' in parts[1] else ''
            free_annotation = parts[2].split('=')[1] if '=' in parts[2] else ''
            
            if not tissue or not cell_ontology:
                continue
                
            cell_data = {
                'organ_tissue': tissue,
                'cell_ontology_class': cell_ontology,
                'free_annotation': free_annotation
            }
            
            if tissue not in candidate_matches:
                candidate_matches[tissue] = []
            
            # 相似度默认为1.0
            candidate_matches[tissue].append((cell_data, 1.0))
            
        except Exception as e:
            print(f"解析条目时出错: {entry}, 错误: {str(e)}")
            continue
    
    return candidate_matches

def generate_prompt(original_tissue, original_cell, candidate_matches):
    """生成组织细胞标准化的prompt"""
    # 构建候选列表的文本描述
    candidate_text = ""
    for i, (tissue, cells) in enumerate(candidate_matches.items()):
        candidate_text += f"\n候选组织 {i+1}: {tissue}\n"
        for j, (cell, score) in enumerate(cells):
            cell_ontology = cell['cell_ontology_class']
            free_annotation = cell['free_annotation']
            candidate_text += f"  候选细胞 {j+1}: cell_ontology_class='{cell_ontology}', free_annotation='{free_annotation}'\n"
    
    prompt = f"""
    你是一个生物医学专家，正在帮助标准化细胞和组织类型的标注。请根据以下原始数据和预检索得到的候选匹配，给出最合适的修正结果。

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

def process_all_cells(input_file, output_path):
    """处理所有需要修正的细胞"""
    # 读取预检索结果
    search_df = pd.read_csv(input_file)
    
    # 初始化结果列表
    results = []
    stats = {
        'total': 0,
        'found': 0,
        'found_tissue': 0,
        'unfound': 0
    }
    
    # 处理每一行数据
    for _, row in tqdm(search_df.iterrows(), total=len(search_df), desc="处理细胞数据"):
        original_tissue = row['ori_tissue']
        original_cell = row['ori_cell_type']
        search_result = row['search_result']
        
        stats['total'] += 1
        
        # 解析候选匹配
        candidate_matches = parse_search_result(search_result)
        
        # 询问大模型进行判断
        prompt = generate_prompt(original_tissue, original_cell, candidate_matches)
        corrected_tissue, corrected_cell, reason = retry_llm_correction(
            original_tissue, original_cell, candidate_matches
        )
        
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
    # args = parse_args()
    # output = args.output
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    # 处理所有细胞
    corrected_df, stats = process_all_cells(input_search_result, output)
    
    # 打印统计信息
    print("\n处理完成！统计信息:")
    print(f"总处理条数: {stats['total']}")
    print(f"完全修正条数(found): {stats['found']}")
    print(f"结果已保存到: {output}")

if __name__ == "__main__":
    main()