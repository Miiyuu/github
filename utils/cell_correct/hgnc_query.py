# from pyhgnc import HGNC
# hgnc = HGNC()
# hgnc.query("former_symbol", "p53")  # 返回标准名称

import json
from mygene import MyGeneInfo
import anndata

h5ad_path = r"D:\0-workingspace\key-marker\data\tabula_sapiens\ts_liver\test.h5ad"

# 加载数据
adata = anndata.read_h5ad(h5ad_path)

# 初始化 MyGeneInfo
mg = MyGeneInfo()

# 存储所有细胞的查询结果
all_cells_query_results = {}

# 遍历每个细胞
for cell_id in adata.obs_names:
    # 获取该细胞的表达数据（稀疏矩阵格式）
    cell_data = adata[cell_id, :].X
    
    # 转换为密集矩阵并筛选高变基因
    cell_expressed_genes = adata.var.loc[
        (adata.var['highly_variable']) & (cell_data.toarray().flatten() > 0),
        'gene_symbol'
    ].tolist()
    
    if not cell_expressed_genes:
        print(f"Cell {cell_id} has no highly variable genes expressed.")
        continue
    
    # 查询基因信息
    try:
        results = mg.querymany(cell_expressed_genes, scopes="symbol,alias", species="human")
        all_cells_query_results[cell_id] = results
        print(f"Processed cell {cell_id}: {len(cell_expressed_genes)} genes queried.")
    except Exception as e:
        print(f"Error querying genes for cell {cell_id}: {e}")
        all_cells_query_results[cell_id] = {"error": str(e)}

# 保存为 JSON 文件
output_json_path = r"D:\0-workingspace\key-marker\data\tabula_sapiens\ts_liver\cell_marker_queries.json"
with open(output_json_path, 'w') as f:
    json.dump(all_cells_query_results, f, indent=4)

print(f"All cell marker gene queries saved to {output_json_path}")