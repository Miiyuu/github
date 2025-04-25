import pandas as pd
import mygene
import json

# 1. 读取原始CSV文件
file_path = r'output\exp_3\marker\corrected_total.csv'
df = pd.read_csv(file_path)
marker_list = df['marker'].tolist()

# 2. 使用mygene查询
mg = mygene.MyGeneInfo()
results = mg.querymany(marker_list, scopes='symbol', species='human')

# 3. 保存所有查询结果为JSON文件
# json_output_file = r'D:\0-workingspace\key-marker\output\mygene_results_100.json'
# with open(json_output_file, 'w') as f:
#     json.dump(results, f, indent=2)

# 4. 创建结果字典（标记是否找到）
result_dict = {item['query']: not item.get('notfound', False) for item in results}

# 5. 创建新DataFrame
output_df = pd.DataFrame({
    'marker': marker_list,
    'in_mygene': [result_dict.get(marker, False) for marker in marker_list]
})

# 6. 保存为CSV
# csv_output_file = r'D:\0-workingspace\key-marker\output\exp_100\marker\cm_marker_mygene_status.csv'
# output_df.to_csv(csv_output_file, index=False)

# print(f"完整查询结果已保存为{json_output_file}")
# print(f"标记状态已保存为{csv_output_file}")
print(f"查询成功率: {output_df['in_mygene'].mean()*100:.2f}%")