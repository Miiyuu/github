import os
import csv
import numpy as np
from tqdm import tqdm
from openai import OpenAI
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity

# 文件路径
standard_file = r"d:\0-workingspace\key-marker\sources\tabula_sapiens\ts_standard.csv"
false_cells_file = r"d:\0-workingspace\key-marker\output\exp_3\cell\false_cells.csv"
output_file = r"d:\0-workingspace\key-marker\memory\exp_3\search_result.csv"
# 新增向量保存路径
standard_emb_file = r"d:\0-workingspace\key-marker\memory\standard_embeddings.npy"
false_cell_emb_file = r"d:\0-workingspace\key-marker\memory\exp_3\false_cell_embeddings.npy"

API_KEY = 'sk-44a071209dad4d2fb2e21827c773e02e'

# 初始化OpenAI客户端
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def generate_sentence_from_standard(row: Dict) -> str:
    """为ts_standard.csv中的一行生成描述性句子"""
    return f"tissue and cell type information: {row['organ_tissue']}, {row['cell_ontology_class']}, {row['free_annotation']}"

def generate_sentence_from_false_cell(row: Dict) -> str:
    """为cm_false_cells.csv中的一行生成描述性句子"""
    return f"tissue and cell type information: {row['ori_tissue']}, {row['ori_cell_type']}"

def get_embedding(text: str) -> List[float]:
    """获取文本的嵌入向量"""
    response = client.embeddings.create(
        model="text-embedding-v3",
        input=text,
        dimensions=1024,
        encoding_format="float"
    )
    return response.data[0].embedding

def save_embeddings(embeddings: np.ndarray, file_path: str):
    """保存嵌入向量到文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    np.save(file_path, embeddings)
    print(f"嵌入向量已保存至: {file_path}")

def load_embeddings(file_path: str) -> np.ndarray:
    """从文件加载嵌入向量"""
    if os.path.exists(file_path):
        print(f"从缓存加载嵌入向量: {file_path}")
        return np.load(file_path)
    return None

def load_and_embed_standard(file_path: str) -> Tuple[List[Dict], np.ndarray]:
    """加载标准数据并生成嵌入向量"""
    # 尝试从缓存加载
    cached_embeddings = load_embeddings(standard_emb_file)
    if cached_embeddings is not None:
        with open(file_path, mode='r', encoding='utf-8') as file:
            standard_data = list(csv.DictReader(file))
        return standard_data, cached_embeddings
    
    standard_data = []
    embeddings = []
    
    # 获取文件总行数用于进度条
    with open(file_path, mode='r', encoding='utf-8') as file:
        total_rows = sum(1 for _ in csv.DictReader(file))
    
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        print(f"\n开始处理标准数据({total_rows}条记录)...")
        for row in tqdm(reader, total=total_rows, desc="生成嵌入向量"):
            standard_data.append(row)
            sentence = generate_sentence_from_standard(row)
            embedding = get_embedding(sentence)
            embeddings.append(embedding)
            # 每100条输出一次进度
            if len(standard_data) % 100 == 0:
                print(f"已处理 {len(standard_data)}/{total_rows} 条标准数据")
    
    print(f"标准数据处理完成，共生成 {len(embeddings)} 个嵌入向量\n")
    # 保存新生成的嵌入向量
    save_embeddings(np.array(embeddings), standard_emb_file)
    return standard_data, np.array(embeddings)

def load_and_embed_false_cells(file_path: str) -> Tuple[List[Dict], np.ndarray]:
    """加载待匹配数据并生成嵌入向量"""
    # 尝试从缓存加载
    cached_embeddings = load_embeddings(false_cell_emb_file)
    if cached_embeddings is not None:
        with open(file_path, mode='r', encoding='utf-8') as file:
            false_cell_data = list(csv.DictReader(file))
        return false_cell_data, cached_embeddings
    
    false_cell_data = []
    embeddings = []
    
    # 获取文件总行数用于进度条
    with open(file_path, mode='r', encoding='utf-8') as file:
        total_rows = sum(1 for _ in csv.DictReader(file))
    
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        print(f"\n开始处理待匹配数据({total_rows}条记录)...")
        for row in tqdm(reader, total=total_rows, desc="生成嵌入向量"):
            false_cell_data.append(row)
            sentence = generate_sentence_from_false_cell(row)
            embedding = get_embedding(sentence)
            embeddings.append(embedding)
            # 每50条输出一次进度
            if len(false_cell_data) % 50 == 0:
                print(f"已处理 {len(false_cell_data)}/{total_rows} 条待匹配数据")
    
    print(f"待匹配数据处理完成，共生成 {len(embeddings)} 个嵌入向量\n")
    # 保存新生成的嵌入向量
    save_embeddings(np.array(embeddings), false_cell_emb_file)
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
            search_result_str = "\n".join(formatted_matches)
            
            writer.writerow({
                'ori_tissue': false_cell['ori_tissue'],
                'ori_cell_type': false_cell['ori_cell_type'],
                'search_result': search_result_str
            })

def main():
    print("\n" + "="*50)
    print("开始细胞组织标准化匹配流程")
    print("="*50 + "\n")
    
    # 加载并嵌入标准数据
    print("Loading and embedding standard data...")
    standard_data, standard_embeddings = load_and_embed_standard(standard_file)
    
    # 加载并嵌入待匹配数据
    print("Loading and embedding false cells data...")
    false_cell_data, false_cell_embeddings = load_and_embed_false_cells(false_cells_file)
    
    # 为每个待匹配数据找到最相似的k个标准数据
    print("\n开始匹配流程...")
    all_search_results = []
    for i, embedding in enumerate(tqdm(false_cell_embeddings, desc="匹配进度")):
        print(f"\n正在处理第 {i+1}/{len(false_cell_embeddings)} 条记录")
        top_matches = find_top_k_matches(embedding, standard_embeddings, standard_data, k=5)
        all_search_results.append(top_matches)
    
    # 保存结果
    print("Saving results...")
    save_results(output_file, false_cell_data, all_search_results)
    print("\n" + "="*50)
    print(f"处理完成！结果已保存至: {output_file}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()