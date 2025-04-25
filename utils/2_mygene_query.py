import pandas as pd
import mygene
import json
import argparse

def main(file_path, json_output, csv_output, false_markers):
    # 1. 读取原始CSV文件
    df = pd.read_csv(file_path)
    marker_list = df['marker'].tolist()

    # 2. 使用mygene查询
    mg = mygene.MyGeneInfo()
    results = mg.querymany(marker_list, scopes='symbol', species='human')

    # 3. 保存所有查询结果为JSON文件
    with open(json_output, 'w') as f:
        json.dump(results, f, indent=2)

    # 4. 创建结果字典（标记是否找到）
    result_dict = {item['query']: not item.get('notfound', False) for item in results}

    # 5. 创建新DataFrame
    output_df = pd.DataFrame({
        'marker': marker_list,
        'in_mygene': [result_dict.get(marker, False) for marker in marker_list]
    })

    # 6. 保存为CSV
    output_df.to_csv(csv_output, index=False)

    # 7. 筛选出false_markers
    false_markers_df = output_df[output_df['in_mygene'] == False]
    false_markers_df.to_csv(false_markers, index=False)

    print(f"查询成功率: {output_df['in_mygene'].mean()*100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", required=True, help="输入CSV文件路径")
    parser.add_argument("--json_output", required=True, help="JSON输出文件路径")
    parser.add_argument("--csv_output", required=True, help="CSV状态输出文件路径")
    parser.add_argument("--false_markers", required=True, help="false markers输出文件路径")
    args = parser.parse_args()
    
    main(args.file_path, args.json_output, args.csv_output, args.false_markers)