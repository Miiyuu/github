import pandas as pd
import pronto

def match_cell_ontology(csv_path, obo_path, output_path):
    # 1. 加载CL本体
    cl = pronto.Ontology(obo_path)
    
    # 2. 读取CSV文件中的细胞名称
    try:
        df = pd.read_csv(csv_path)
        cell_names = df['cell_name'].unique()
    except Exception as e:
        print(f"读取CSV文件出错: {e}")
        return None
    
    # 3. 准备结果数据框
    result_df = pd.DataFrame(columns=['original_cell_name', 'cell_ontology'])
    matched_count = 0
    
    # 4. 遍历每个细胞名称进行匹配
    for cell in cell_names:
        matched = False
        # 检查name字段
        for term in cl.terms():
            if term.name and cell.lower() == term.name.lower():
                result_df.loc[len(result_df)] = [cell, term.id]
                matched = True
                matched_count += 1
                break
        
        # 如果name不匹配，检查synonym字段
        if not matched:
            for term in cl.terms():
                if term.synonyms:
                    for syn in term.synonyms:
                        if cell.lower() == syn.description.lower():
                            result_df.loc[len(result_df)] = [cell, term.id]
                            matched = True
                            matched_count += 1
                            break
                    if matched:
                        break
        
        # 如果仍未匹配，记录未匹配的细胞
        if not matched:
            result_df.loc[len(result_df)] = [cell, None]
    
    # 5. 保存未匹配的细胞到CSV
    unmatched_df = result_df[result_df['cell_ontology'].isna()]
    unmatched_df.to_csv(output_path, index=False)
    
    # 6. 计算匹配概率
    total_cells = len(cell_names)
    match_probability = (matched_count / total_cells) * 100
    
    return match_probability

# 使用示例
csv_path = r"D:\0-workingspace\key-marker\data\markers_human\total.csv"
obo_path = r"D:\0-workingspace\key-marker\sources\cell_ontology\Ontology_data\cl.obo"
output_path = r"D:\0-workingspace\key-marker\output\unmatched_cells.csv"

probability = match_cell_ontology(csv_path, obo_path, output_path)
print(f"细胞匹配概率: {probability:.2f}%")