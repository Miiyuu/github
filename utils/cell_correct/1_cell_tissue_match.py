import pandas as pd
import os
import argparse
import re
import numpy as np

# 定义全局文件路径
# ts_standard = r"sources\tabula_sapiens\ts_standard.csv"
# corrected_total = r"output\exp_100\marker\corrected_total.csv"
# matched_output = r"output\exp_100\cell\matched_tissue_cell.csv"
# false_output = r"output\exp_100\cell\false_cells.csv"
# filter_output = r"output\exp_100\cell\filter_total.csv"

# def create_standardized_df():
#     """
#     创建标准化DataFrame，整合ontology-free和tissue-cell文件中的信息
#     返回包含organ_tissue, cell_ontology_class, free_annotation的标准化DataFrame
#     """
#     # 读取ontology-free文件，取organ_tissue和cell_ontology_class列
#     df_ontology = pd.read_csv(TISSUE_CELL_PATH, usecols=['organ_tissue', 'cell_ontology_class'])
#     # 转换为小写
#     df_ontology = df_ontology.apply(lambda x: x.str.lower())
#     # 去除重复行
#     df_ontology = df_ontology.drop_duplicates()
    
#     # 读取tissue-cell文件，取cell_ontology_class和free_annotation列
#     df_tissue_cell = pd.read_csv(ONTOLOGY_FREE_PATH, usecols=['cell_ontology_class', 'free_annotation'])
#     # 转换为小写
#     df_tissue_cell = df_tissue_cell.apply(lambda x: x.str.lower())
#     # 去除重复行
#     df_tissue_cell = df_tissue_cell.drop_duplicates()
    
#     # 合并两个DataFrame，以cell_ontology_class为键
#     df_standard = pd.merge(df_ontology, df_tissue_cell, on='cell_ontology_class', how='left')
    
#     return df_standard

def parse_args():
    parser = argparse.ArgumentParser(description='细胞组织匹配工具')
    parser.add_argument('--ts_standard', required=True, help='标准数据文件路径')
    parser.add_argument('--corrected_total', required=True, help='待匹配数据文件路径')
    parser.add_argument('--matched_output', required=True, help='匹配成功输出文件路径')
    parser.add_argument('--false_output', required=True, help='匹配失败输出文件路径')
    parser.add_argument('--filter_output', required=True, help='过滤后数据输出文件路径')
    return parser.parse_args()

def process_corrected_data(df_standard, corrected_total_path, filter_output_path):
    """
    处理corrected_total数据，创建df_corrected DataFrame
    :param df_standard: 标准化DataFrame
    :return: (df_corrected DataFrame, 统计信息字典)
    """
    # 读取corrected_total文件
    df_corrected_total = pd.read_csv(corrected_total_path)
    
    # 初始化统计字典
    stats = {
        'original_total': len(df_corrected_total),
        'human_total': 0,
        'tissue_missing': 0,
        'cell_missing': 0,
        'both_missing': 0,
        'final_total': 0,
        'matched_count': 0
    }
    
    # 筛选species=human的数据
    df_human = df_corrected_total[df_corrected_total['species'].str.lower() == 'human'].copy()
    stats['human_total'] = len(df_human)
    
    # 检查空值并统计
    tissue_missing = df_human['tissue_type'].isna()
    cell_missing = df_human['cell_name'].isna()
    
    stats['tissue_missing'] = tissue_missing.sum()
    stats['cell_missing'] = cell_missing.sum()
    stats['both_missing'] = (tissue_missing & cell_missing).sum()
    
    # 去除tissue_type或cell_name为空的数据
    df_human = df_human.dropna(subset=['tissue_type', 'cell_name'])
    stats['final_total'] = len(df_human)
    
    # 保存过滤后的数据到新文件
    df_human.to_csv(filter_output_path, index=False)
    
    # 转换为小写
    df_human['tissue_type'] = df_human['tissue_type'].str.lower()
    df_human['cell_name'] = df_human['cell_name'].str.lower()
    
    # 初始化df_corrected
    df_corrected = pd.DataFrame(columns=[
        'ori_tissue', 
        'ori_cell_type', 
        'corrected_tissue', 
        'corrected_cell_type', 
        'corrected'
    ])
    
    # 遍历human数据
    for _, row in df_human.iterrows():
        tissue = row['tissue_type']
        cell = row['cell_name']
        
        # 在标准化df中查找匹配的organ_tissue
        matched_tissues = df_standard[df_standard['organ_tissue'] == tissue]
        
        if not matched_tissues.empty:
            # 获取该organ_tissue下的所有cell_ontology_class和free_annotation
            possible_cell_ontology = matched_tissues['cell_ontology_class'].tolist()
            possible_free_annotation = matched_tissues['free_annotation'].dropna().tolist()
            all_possible_cell_names = possible_cell_ontology + possible_free_annotation
            
            # 检查cell_name是否匹配任一cell名称
            if cell in all_possible_cell_names:
                # 完全匹配的情况
                stats['matched_count'] += 1
                # 获取对应的cell_ontology_class（优先使用完全匹配的，否则从free_annotation映射）
                if cell in possible_cell_ontology:
                    corrected_cell_type = cell
                else:
                    # 从free_annotation映射回cell_ontology_class
                    corrected_cell_type = matched_tissues[
                        matched_tissues['free_annotation'] == cell
                    ]['cell_ontology_class'].values[0]
                
                # 添加到df_corrected
                new_row = {
                    'ori_tissue': tissue,
                    'ori_cell_type': cell,
                    'corrected_tissue': tissue,  # 因为organ_tissue已完全匹配
                    'corrected_cell_type': corrected_cell_type,
                    'corrected': True
                }
                df_corrected = pd.concat([df_corrected, pd.DataFrame([new_row])], ignore_index=True)
                continue
        
        # 不匹配的情况
        new_row = {
            'ori_tissue': tissue,
            'ori_cell_type': cell,
            'corrected_tissue': None,
            'corrected_cell_type': None,
            'corrected': False
        }
        df_corrected = pd.concat([df_corrected, pd.DataFrame([new_row])], ignore_index=True)
    
    # 计算匹配率
    stats['match_rate'] = stats['matched_count'] / stats['final_total'] if stats['final_total'] > 0 else 0
    
    return df_corrected, stats

def main():
    args = parse_args()
    
    # 读取标准数据
    df_standard = pd.read_csv(args.ts_standard)
    
    # 处理corrected_total数据
    df_corrected, stats = process_corrected_data(df_standard, args.corrected_total, args.filter_output)
    
    # 保存结果
    df_corrected.to_csv(args.matched_output, index=False)

    # 保存 false_cells
    false_cells = df_corrected[df_corrected['corrected'] == False]
    false_cells[['ori_tissue', 'ori_cell_type']].to_csv(args.false_output, index=False)
    
    # 输出统计信息
    print("\n===== 数据处理统计 =====")
    print(f"原始数据总条数: {stats['original_total']}")
    print(f"human数据条数: {stats['human_total']}")
    print(f"  - tissue_type缺失: {stats['tissue_missing']} 条")
    print(f"  - cell_name缺失: {stats['cell_missing']} 条")
    print(f"去除空值后有效数据: {stats['final_total']} 条")
    print(f"\n过滤后的数据已保存到: {args.filter_output}")
    
    print("\n===== 匹配统计结果 =====")
    print(f"匹配条数: {stats['matched_count']}")
    print(f"匹配率: {stats['match_rate']:.2%}")
    print(f"\n处理完成，结果已保存到: {args.matched_output}")

if __name__ == "__main__":
    main()