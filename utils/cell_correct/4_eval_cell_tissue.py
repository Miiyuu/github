import pandas as pd
import os

# 读取两个CSV文件
cm_path = r"output\exp_3\marker\cm_corrected_total.csv"
test_path = r"output\exp_3\marker\corrected_total_0409.csv"
output_path = r"output\exp_3\marker\after_result.csv"

# 读取数据
standard_df = pd.read_csv(cm_path)
test_df = pd.read_csv(test_path)

# 确保列名一致
standard_df.columns = standard_df.columns.str.strip()
test_df.columns = test_df.columns.str.strip()

# 按pmid分组
standard_groups = standard_df.groupby('pmid')
test_groups = test_df.groupby('pmid')

results = []

# 遍历每个pmid组
for pmid, standard_group in standard_groups:
    if pmid in test_groups.groups:
        test_group = test_groups.get_group(pmid)
        
        # 计算marker召回率
        standard_markers = set(standard_group['marker'].dropna().unique())
        test_markers = set(test_group['marker'].dropna().unique())
        
        if len(standard_markers) > 0:
            marker_recall = len(standard_markers & test_markers) / len(standard_markers)
        else:
            marker_recall = 0.0
        
        # 计算tissue_cell召回率
        standard_tc = set(zip(standard_group['tissue_type'].fillna(''), 
                             standard_group['cell_name'].fillna('')))
        test_tc = set(zip(test_group['tissue_type'].fillna(''), 
                         test_group['cell_name'].fillna('')))
        
        if len(standard_tc) > 0:
            tc_recall = len(standard_tc & test_tc) / len(standard_tc)
        else:
            tc_recall = 0.0
        
        results.append({
            'pmid': pmid,
            'marker_recall': marker_recall,
            'tissue_cell_recall': tc_recall,
            'standard_marker_count': len(standard_markers),
            'test_marker_count': len(test_markers),
            'standard_tc_count': len(standard_tc),
            'test_tc_count': len(test_tc)
        })
    else:
        # 如果在测试数据中没有找到该pmid，则召回率为0
        standard_markers = set(standard_group['marker'].dropna().unique())
        standard_tc = set(zip(standard_group['tissue_type'].fillna(''), 
                             standard_group['cell_name'].fillna('')))
        
        results.append({
            'pmid': pmid,
            'marker_recall': 0.0,
            'tissue_cell_recall': 0.0,
            'standard_marker_count': len(standard_markers),
            'test_marker_count': 0,
            'standard_tc_count': len(standard_tc),
            'test_tc_count': 0
        })

# 创建结果DataFrame
result_df = pd.DataFrame(results)

# 计算平均召回率
avg_marker_recall = result_df['marker_recall'].mean()
avg_tc_recall = result_df['tissue_cell_recall'].mean()

# 计算所有文章中的marker总召回率
total_standard_markers = set()
total_test_markers = set()
for index, row in result_df.iterrows():
    total_standard_markers.update(set(standard_df[standard_df['pmid'] == row['pmid']]['marker'].dropna().unique()))
    total_test_markers.update(set(test_df[test_df['pmid'] == row['pmid']]['marker'].dropna().unique()))

total_marker_recall = len(total_standard_markers & total_test_markers) / len(total_standard_markers) if len(total_standard_markers) > 0 else 0.0

# 计算所有文章中的tissue_cell总召回率
total_standard_tc = set()
total_test_tc = set()
for index, row in result_df.iterrows():
    total_standard_tc.update(set(zip(standard_df[standard_df['pmid'] == row['pmid']]['tissue_type'].fillna(''), 
                                     standard_df[standard_df['pmid'] == row['pmid']]['cell_name'].fillna(''))))
    total_test_tc.update(set(zip(test_df[test_df['pmid'] == row['pmid']]['tissue_type'].fillna(''), 
                                 test_df[test_df['pmid'] == row['pmid']]['cell_name'].fillna(''))))

total_tc_recall = len(total_standard_tc & total_test_tc) / len(total_standard_tc) if len(total_standard_tc) > 0 else 0.0

# 添加平均行
avg_row = pd.DataFrame({
    'pmid': ['Average'],
    'marker_recall': [avg_marker_recall],
    'tissue_cell_recall': [avg_tc_recall],
    'standard_marker_count': [result_df['standard_marker_count'].sum()],
    'test_marker_count': [result_df['test_marker_count'].sum()],
    'standard_tc_count': [result_df['standard_tc_count'].sum()],
    'test_tc_count': [result_df['test_tc_count'].sum()]
})

# 添加total行
total_row = pd.DataFrame({
    'pmid': ['Total'],
    'marker_recall': [total_marker_recall],
    'tissue_cell_recall': [total_tc_recall],
    'standard_marker_count': [len(total_standard_markers)],
    'test_marker_count': [len(total_test_markers)],
    'standard_tc_count': [len(total_standard_tc)],
    'test_tc_count': [len(total_test_tc)]
})

result_df = pd.concat([result_df, avg_row, total_row], ignore_index=True)

# 确保输出目录存在
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# 保存结果
result_df.to_csv(output_path, index=False)

print(f"结果已保存到 {output_path}")
print(f"平均marker召回率: {avg_marker_recall:.4f}")
print(f"平均tissue_cell召回率: {avg_tc_recall:.4f}")
print(f"所有文章中的marker总召回率: {total_marker_recall:.4f}")
print(f"所有文章中的tissue_cell总召回率: {total_tc_recall:.4f}")