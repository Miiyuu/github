import pandas as pd
import numpy as np
import ast
from tabulate import tabulate  # 用于在控制端以表格形式输出

def load_grouped_markers(file_path):
    """
    加载 grouped_total.csv 文件，返回一个字典，键为 (pmid, species, tissue_type, cell_name)，值为 markers 列表。
    """
    grouped_df = pd.read_csv(file_path)
    marker_dict = {}
    for _, row in grouped_df.iterrows():
        key = (row['pmid'], row['species'], row['tissue_type'], row['cell_name'])
        # 将字符串形式的列表转换为 Python 列表
        markers = ast.literal_eval(row['markers'])
        marker_dict[key] = markers
    return marker_dict

def assign_marker_weights(markers):
    """
    为 marker 列表分配权重。权重按顺序递减，第一个 marker 权重最高。
    """
    if not markers:
        return {}
    weights = np.linspace(1.0, 0.1, num=len(markers))  # 权重从 1.0 递减到 0.1
    return dict(zip(markers, weights))

# TODO: 匹配方式优化
def match_cluster_to_cell_type(cluster_degs, marker_dict):
    """
    将 cluster 的 DEGs 与 marker 列表匹配，计算每个细胞类别的得分。
    """
    scores = {}
    for key, markers in marker_dict.items():
        # 分配权重
        weights = assign_marker_weights(markers)
        
        # 计算得分
        score = 0
        for i, deg in enumerate(cluster_degs):
            if deg in weights:
                # 得分 = marker 权重 / (DEG 排名 + 1)
                score += weights[deg] / (i + 1)
        scores[key] = score
    
    # 返回得分最高的细胞类别
    if scores:
        best_match = max(scores, key=scores.get)
        return best_match, scores[best_match]
    else:
        return None, 0

def annotate_clusters(cluster_degs_dict, marker_dict, top_k=3):
    """
    为所有 cluster 注释细胞类别，并返回前 k 个结果。
    """
    annotations = []
    for cluster, degs in cluster_degs_dict.items():
        # 获取所有匹配结果
        results = []
        for key, markers in marker_dict.items():
            weights = assign_marker_weights(markers)
            score = 0
            for i, deg in enumerate(degs):
                if deg in weights:
                    score += weights[deg] / (i + 1)
            results.append({
                'cluster': cluster,
                'degs': degs,
                'annotated_species': key[1],
                'annotated_tissue': key[2],
                'annotated_cell_type': key[3],
                'reference_markers': markers,
                'score': score
            })
        
        # 按得分排序，取前 k 个结果
        results.sort(key=lambda x: x['score'], reverse=True)
        annotations.extend(results[:top_k])
    
    return annotations

def save_and_display_results(annotations, output_csv):
    """
    将结果保存为 CSV 文件，并以表格形式输出到控制端。
    """
    # 转换为 DataFrame
    df = pd.DataFrame(annotations)
    
    # 保存为 CSV 文件
    df.to_csv(output_csv, index=False)
    
    # 以表格形式输出到控制端
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))

# 示例调用
if __name__ == "__main__":
    # 加载 grouped_total.csv
    marker_dict = load_grouped_markers(r"D:\0-workingspace\key-marker\data\markers_human\grouped_total.csv")
    
    # 假设 cluster_degs_dict 是每个 cluster 的 DEGs 列表
    cluster_degs_dict = {
        'cluster_0': ['C1QC', 'CXCL9', 'CXCL10'],  
        'cluster_1': ['SPP1', 'C1QC', 'NLRP3']
    }
    
    annotations = annotate_clusters(cluster_degs_dict, marker_dict, top_k=5)
    
    # 保存结果并显示
    save_and_display_results(annotations, output_csv=r"D:\0-workingspace\key-marker\output\tmp\cluster_annotations.csv")