import os
import pandas as pd
import argparse

def merge_excel_files(input_dir, output_file):
    """
    合并目录下的所有 Excel 文件，并新增 pmid 列。
    """
    excel_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
    total_df = pd.DataFrame()
    for file in excel_files:
        pmid = os.path.splitext(file)[0]
        file_path = os.path.join(input_dir, file)
        df = pd.read_excel(file_path)
        df['pmid'] = pmid
        total_df = pd.concat([total_df, df], ignore_index=True)
    
    total_df.to_csv(output_file, index=False)
    print(f"All files merged and saved to {output_file}")

def group_and_combine_markers(input_file, output_file):
    """
    按照 pmid, species, tissue_type, cell_name 分组，并合并 marker 列。
    考虑 species 或 tissue_type 为 null 的情况。
    """
    total_df = pd.read_csv(input_file)
    
    # 使用 fillna 填充 null 值，或者使用 dropna=False 保留 null 值
    grouped_df = total_df.groupby(
        ['pmid', 'species', 'tissue_type', 'cell_name'], dropna=False
    )['marker'].apply(list).reset_index()
    
    grouped_df.rename(columns={'marker': 'markers'}, inplace=True)
    grouped_df.to_csv(output_file, index=False)
    print(f"Grouped data saved to {output_file}")

def main(input_dir, output_file, grouped_output_file):
    merge_excel_files(input_dir, output_file)
    group_and_combine_markers(output_file, grouped_output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True, help="输入目录路径")
    parser.add_argument("--output_file", required=True, help="合并后CSV输出文件路径")
    parser.add_argument("--grouped_output_file", required=True, help="分组后CSV输出文件路径")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_file, args.grouped_output_file)