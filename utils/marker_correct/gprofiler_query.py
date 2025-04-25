import pandas as pd
from gprofiler import GProfiler

# 1. 读取原始CSV文件
file_path = r'D:\0-workingspace\key-marker\output\exp_100\marker\corrected_total_0409.csv'
df = pd.read_csv(file_path)
marker_list = df['marker'].tolist()

# 2. 使用gprofiler查询
gp = GProfiler(return_dataframe=True)

# 分批处理（g:Profiler可能有查询限制）
batch_size = 100  # 可根据API限制调整
results = []
for i in range(0, len(marker_list), batch_size):
    batch = marker_list[i:i + batch_size]
    try:
        batch_result = gp.convert(
            query=batch,
            organism="hsapiens"
        )
        print(batch_result)
        results.append(batch_result)
    except Exception as e:
        print(f"处理批次 {i//batch_size} 时出错: {e}")
        # 对于出错批次，创建包含notfound标记的结果
        error_results = [{'query': gene, 'notfound': True} for gene in batch]
        results.append(pd.DataFrame(error_results))

# 合并所有批次结果
all_results = pd.concat(results) if results else pd.DataFrame()

# 3. 保存所有查询结果为JSON文件（可选）
# json_output_file = r'D:\0-workingspace\key-marker\output\gprofiler_results_100.json'
# all_results.to_json(json_output_file, orient='records', indent=2)

# 4. 创建结果字典（标记是否找到）
# g:Profiler成功转换的基因会有'converted'列
result_dict = all_results.groupby('query').apply(
    lambda x: not x['notfound'].any() if 'notfound' in x.columns else True
).to_dict()

# 5. 创建新DataFrame
output_df = pd.DataFrame({
    'marker': marker_list,
    'in_gprofiler': [result_dict.get(marker, False) for marker in marker_list]
})

# 6. 保存为CSV
# csv_output_file = r'D:\0-workingspace\key-marker\output\exp_100\correct_marker_gprofiler_status.csv'
# output_df.to_csv(csv_output_file, index=False)

# print(f"完整查询结果已保存为{json_output_file}")
# print(f"标记状态已保存为{csv_output_file}")
print(f"查询成功率: {output_df['in_gprofiler'].mean()*100:.2f}%")