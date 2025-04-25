import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='基因标记标准化工具')
    parser.add_argument('--total_csv', required=True, help='原始total.csv文件路径')
    parser.add_argument('--corrected_markers', required=True, help='修正后的markers文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    return parser.parse_args()

def replace_markers(total_df, marker_mapping):
    # 复制原始列用于比较
    original_markers = total_df['marker'].copy()
    
    # 应用替换
    total_df['marker'] = total_df['marker'].apply(lambda x: marker_mapping.get(x, x))
    
    # 计算被修改的行数
    changed_rows = (original_markers != total_df['marker']).sum()
    return total_df, changed_rows

def main():
    args = parse_args()
    
    # 读取文件
    total_df = pd.read_csv(args.total_csv)
    marker_mapping_df = pd.read_csv(args.corrected_markers)
    
    # 创建映射字典
    marker_mapping = dict(zip(marker_mapping_df['original'], marker_mapping_df['corrected']))
    
    # 替换标记
    corrected_df, changed_rows = replace_markers(total_df, marker_mapping)
    
    # 保存结果
    corrected_df.to_csv(args.output, index=False)
    
    # 打印结果
    print(f"已完成标记标准化，共修改 {changed_rows} 处基因符号")
    print(f"文件已保存至: {args.output}")

if __name__ == "__main__":
    main()