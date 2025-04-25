import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='细胞组织标准化修正工具')
    parser.add_argument('--cell_tissue_corrected', required=True, help='修正后的细胞组织数据文件路径')
    parser.add_argument('--filter_path', required=True, help='待修正的过滤数据文件路径')
    parser.add_argument('--marker_total', required=True, help='待修正的标记总数据文件路径')
    parser.add_argument('--filter_corrected', required=True, help='修正后的过滤数据输出路径')
    parser.add_argument('--corrected', required=True, help='修正后的总数据输出路径')
    return parser.parse_args()

def create_correction_dict(cell_tissue_corrected_path):
    """创建修正字典"""
    cell_df = pd.read_csv(cell_tissue_corrected_path)
    filtered_cell = cell_df[cell_df['status'] == 'found'][['ori_tissue', 'ori_cell_type', 'corrected_tissue', 'corrected_cell']]
    
    correction_dict = {}
    for _, row in filtered_cell.iterrows():
        key = (str(row['ori_tissue']).lower(), str(row['ori_cell_type']).lower())
        value = (row['corrected_tissue'], row['corrected_cell'])
        correction_dict[key] = value
    return correction_dict

def process_file(input_path, output_path, correction_dict):
    """处理单个文件并返回统计信息"""
    df = pd.read_csv(input_path)
    total = len(df)
    cnt = 0
    
    for idx, row in df.iterrows():
        key = (str(row['tissue_type']).lower(), str(row['cell_name']).lower())
        if key in correction_dict:
            cnt += 1
            corrected_tissue, corrected_cell = correction_dict[key]
            df.at[idx, 'tissue_type'] = corrected_tissue
            df.at[idx, 'cell_name'] = corrected_cell
    
    df.to_csv(output_path, index=False)
    # correction_rate = cnt / total * 100 if total > 0 else 0
    return total, cnt

def main():
    args = parse_args()
    
    # 创建修正字典
    correction_dict = create_correction_dict(args.cell_tissue_corrected)
    
    # 处理filter_total.csv
    total1, cnt1 = process_file(args.filter_path, args.filter_corrected, correction_dict)
    print(f"filter_total.csv - 原始记录: {total1}条, 修正记录: {cnt1}条")
    
    # 处理corrected_total.csv
    total2, cnt2= process_file(args.marker_total, args.corrected, correction_dict)
    print(f"corrected_total.csv - 原始记录: {total2}条, 修正记录: {cnt2}条")
    
    print("处理完成，结果已保存到指定路径")

if __name__ == "__main__":
    main()