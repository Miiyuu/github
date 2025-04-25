import scanpy as sc
import pronto
import pandas as pd

def match_cell_ontology(h5ad_path, obo_path, output_path):
    # 1. 加载h5ad文件
    try:
        adata = sc.read_h5ad(h5ad_path)
        if 'cell_ontology_class' not in adata.obs.columns:
            raise ValueError("h5ad文件中未找到cell_ontology_class列")
        cell_ontologies = adata.obs['cell_ontology_class'].unique()
        # cell_ontologies = adata.obs['free_annotation'].unique()
    except Exception as e:
        print(f"读取h5ad文件出错: {e}")
        return None

    # 2. 加载CL本体
    cl = pronto.Ontology(obo_path)
    
    # 3. 准备结果数据框
    result_df = pd.DataFrame(columns=['original_cell_name', 'cell_ontology'])
    matched_count = 0
    
    # 4. 匹配逻辑
    for cell in cell_ontologies:
        if pd.isna(cell):  # 跳过空值
            continue
            
        matched = False
        # 检查term的name和synonym
        for term in cl.terms():
            # 检查name
            if term.name and cell.lower() == term.name.lower():
                result_df.loc[len(result_df)] = [cell, term.id]
                matched = True
                matched_count += 1
                break
                
            # 检查synonym
            if term.synonyms:
                for syn in term.synonyms:
                    if cell.lower() == str(syn).lower():
                        result_df.loc[len(result_df)] = [cell, term.id]
                        matched = True
                        matched_count += 1
                        break
                if matched:
                    break
        
        # 未匹配的记录
        if not matched:
            result_df.loc[len(result_df)] = [cell, None]
    
    # 5. 保存未匹配的细胞
    unmatched_df = result_df[result_df['cell_ontology'].isna()]
    unmatched_df.to_csv(output_path, index=False)
    
    # 6. 计算匹配概率
    total_cells = len(cell_ontologies)
    match_probability = (matched_count / total_cells) * 100 if total_cells > 0 else 0
    
    return match_probability

# 使用示例
h5ad_path = "D:/0-workingspace/key-marker/data/tabula_sapiens/ts_liver/test.h5ad"
obo_path = "D:/0-workingspace/key-marker/sources/cell_ontology/Ontology_data/cl.obo"
output_path = "unmatched_cell_ontology_tsliver.csv"

probability = match_cell_ontology(h5ad_path, obo_path, output_path)
print(f"细胞本体匹配概率: {probability:.2f}%")