import os
import csv
import numpy as np
from tqdm import tqdm
from openai import OpenAI
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity

# 文件路径配置
false_cells_path = r"D:\0-workingspace\key-marker\output\exp_100\cell\false_cells.csv"
output_file = r"d:\0-workingspace\key-marker\memory\exp_100\search_result.csv"

standard_emb_file = r"d:\0-workingspace\key-marker\memory\standard_embeddings.npy"
standard_data_file = r"d:\0-workingspace\key-marker\sources\tabula_sapiens\ts_standard.csv"

def load_standard_data() -> Tuple[List[Dict], np.ndarray]:
    """加载预先生成的标准数据嵌入向量"""
    if not os.path.exists(standard_emb_file):
        raise FileNotFoundError(f"标准嵌入向量文件 {standard_emb_file} 不存在")
    
    print(f"从缓存加载标准嵌入向量: {standard_emb_file}")
    standard_embeddings = np.load(standard_emb_file)
    
    with open(standard_data_file, mode='r', encoding='utf-8') as file:
        standard_data = list(csv.DictReader(file))
    
    print(f"已加载 {len(standard_data)} 条标准数据和 {len(standard_embeddings)} 个嵌入向量")
    return standard_data, standard_embeddings

def process_false_cells(false_cells_path: str) -> Tuple[List[Dict], np.ndarray]:
    """处理新的false_cells文件并生成嵌入向量"""
    false_cell_emb_file = os.path.join(
        os.path.dirname(false_cells_path),
        "false_cell_embeddings.npy"
    )
    
    # 初始化OpenAI客户端
    client = OpenAI(
        api_key='sk-44a071209dad4d2fb2e21827c773e02e',
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    false_cell_data = []
    embeddings = []
    
    # 获取文件总行数
    with open(false_cells_path, mode='r', encoding='utf-8') as file:
        total_rows = sum(1 for _ in csv.DictReader(file))
    
    with open(false_cells_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        print(f"\n开始处理待匹配数据({total_rows}条记录)...")
        for row in tqdm(reader, total=total_rows, desc="生成嵌入向量"):
            false_cell_data.append(row)
            sentence = f"tissue and cell type: {row['ori_tissue']}, {row['ori_cell_type']}"
            embedding = client.embeddings.create(
                model="text-embedding-v3",
                input=sentence,
                dimensions=1024
            ).data[0].embedding
            embeddings.append(embedding)
    
    # 保存新生成的嵌入向量
    os.makedirs(os.path.dirname(false_cell_emb_file), exist_ok=True)
    np.save(false_cell_emb_file, np.array(embeddings))
    print(f"待匹配数据处理完成，嵌入向量已保存至: {false_cell_emb_file}")
    
    return false_cell_data, np.array(embeddings)

def find_top_k_matches(query_embedding: np.ndarray, standard_embeddings: np.ndarray, 
                      standard_data: List[Dict], k: int = 5) -> List[Dict]:
    """找到与查询向量最相似的k个标准数据"""
    # 计算余弦相似度
    similarities = cosine_similarity(query_embedding.reshape(1, -1), standard_embeddings)[0]
    
    # 获取前k个最相似的索引
    top_k_indices = np.argsort(similarities)[-k:][::-1]
    
    # 输出匹配质量信息
    top_scores = similarities[top_k_indices]
    print(f"最佳匹配相似度: {top_scores[0]:.4f}, 平均相似度: {np.mean(top_scores):.4f}")
    
    return [standard_data[i] for i in top_k_indices]

def save_results(output_path: str, false_cell_data: List[Dict], search_results: List[List[Dict]]) -> None:
    """保存匹配结果到CSV文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ['ori_tissue', 'ori_cell_type', 'search_result']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        for false_cell, matches in zip(false_cell_data, search_results):
            # 格式化匹配结果
            formatted_matches = []
            for match in matches:
                formatted = f"organ_tissue={match['organ_tissue']}, cell_ontology_class={match['cell_ontology_class']}, free_annotation={match['free_annotation']}"
                formatted_matches.append(formatted)
            
            # 将多条匹配结果用分号连接
            search_result_str = "; ".join(formatted_matches)
            
            writer.writerow({
                'ori_tissue': false_cell['ori_tissue'],
                'ori_cell_type': false_cell['ori_cell_type'],
                'search_result': search_result_str
            })

def main(false_cells_path: str):
    print("\n" + "="*50)
    print("细胞组织标准化匹配流程 (优化版)")
    print("="*50 + "\n")
    
    # 1. 加载预生成的标准数据
    standard_data, standard_embeddings = load_standard_data()
    
    # 2. 处理新的false_cells文件
    false_cell_data, false_cell_embeddings = process_false_cells(false_cells_path)
    
    # 3. 执行匹配流程
    print("\n开始匹配流程...")
    all_search_results = []
    for i, embedding in enumerate(tqdm(false_cell_embeddings, desc="匹配进度")):
        top_matches = find_top_k_matches(embedding, standard_embeddings, standard_data, k=5)
        all_search_results.append(top_matches)
    
    # 4. 保存结果
    save_results(output_file, false_cell_data, all_search_results)
    print(f"\n处理完成！结果已保存至: {output_file}")

if __name__ == "__main__":
    import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument("false_cells_path", help="待匹配的false_cells文件路径")
    # args = parser.parse_args()
    # main(args.false_cells_path)
    main(false_cells_path)