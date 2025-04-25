import scanpy as sc
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

def preprocess_scRNAseq(data_path, output_dir):
    """
    预处理scRNA-seq数据，包括标准化、筛选高变基因、降维聚类和差异表达分析。
    """
    # 检查输入文件是否存在
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"File not found: {data_path}")
    if not os.path.isfile(data_path):
        raise ValueError(f"Path is not a file: {data_path}")
    
    # 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(output_dir):
        print(f"Output directory does not exist. Creating directory: {output_dir}")
        os.makedirs(output_dir)

    # 读取scRNA-seq数据
    adata = sc.read(data_path)
    
    # 数据标准化
    if np.max(adata.X) > 1000:  # 如果数据最大值大于1000，可能是原始计数数据
        print("Performing log normalization...")
        sc.pp.normalize_total(adata, target_sum=1e4)  # 对数归一化
        sc.pp.log1p(adata)  # 对数转换
    else:
        print("Data is already log-normalized. Skipping log normalization.")
    
    # 筛选高变基因
    adata = filter_highly_variable_genes(adata, output_dir)
    
    # 降维和聚类
    adata = reduce_dimension_and_cluster(adata)
    
    # 保存细胞簇信息
    save_cluster_info(adata, output_dir)
    
    # 保存聚类图
    save_cluster_plot(adata, output_dir)
    
    # 差异表达分析
    perform_differential_expression_analysis(adata, output_dir)
    
    return adata

def filter_highly_variable_genes(adata, output_dir):
    """
    筛选高变基因，并保存筛选后的基因列表。
    """
    print("Filtering highly variable genes...")
    sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
    adata = adata[:, adata.var.highly_variable]  # 保留高变基因
    
    # 保存高变基因列表
    highly_variable_genes = adata.var_names[adata.var.highly_variable]
    pd.DataFrame(highly_variable_genes, columns=['gene']).to_csv(
        os.path.join(output_dir, 'highly_variable_genes.csv'), index=False
    )
    print(f"Highly variable genes saved to {os.path.join(output_dir, 'highly_variable_genes.csv')}")
    
    return adata

def reduce_dimension_and_cluster(adata):
    """
    降维和聚类。
    """
    print("Reducing dimensions and clustering...")
    sc.pp.scale(adata, max_value=10)  # Z-score标准化
    sc.tl.pca(adata, svd_solver='arpack')  # PCA降维
    sc.pp.neighbors(adata, n_pcs=30)  # 构建KNN图
    sc.tl.umap(adata)  # UMAP降维
    
    # 聚类
    sc.tl.leiden(adata, resolution=0.5)  # Leiden聚类
    adata.obs['cluster'] = adata.obs['leiden']  # 将聚类结果存储到adata.obs中
    
    return adata

def save_cluster_info(adata, output_dir):
    """
    保存细胞簇的相关信息，包括聚类标签和UMAP坐标。
    """
    print("Saving cluster information...")
    cluster_info = adata.obs[['cluster']].copy()
    cluster_info['UMAP_1'] = adata.obsm['X_umap'][:, 0]
    cluster_info['UMAP_2'] = adata.obsm['X_umap'][:, 1]
    cluster_info.to_csv(os.path.join(output_dir, 'cluster_info.csv'))
    print(f"Cluster information saved to {os.path.join(output_dir, 'cluster_info.csv')}")

def save_cluster_plot(adata, output_dir):
    """
    保存聚类图。
    """
    print("Saving cluster plot...")
    sc.pl.umap(adata, color='cluster', legend_loc='on data', frameon=False, title='Clustering Result', show=False)
    plt.savefig(os.path.join(output_dir, 'cluster_plot.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Cluster plot saved to {os.path.join(output_dir, 'cluster_plot.png')}")

def perform_differential_expression_analysis(adata, output_dir):
    """
    差异表达分析，保存每个簇的差异上调基因。
    """
    print("Performing differential expression analysis...")
    sc.tl.rank_genes_groups(adata, 'cluster', method='wilcoxon')  # Wilcoxon检验
    
    # 保存每个簇的差异上调基因
    for cluster in adata.obs['cluster'].unique():
        # 获取差异表达基因
        degs = sc.get.rank_genes_groups_df(adata, group=cluster)
        degs = degs[degs['pvals_adj'] < 0.05]  # 筛选显著差异基因
        degs = degs.sort_values(by='scores', ascending=False)  # 按得分排序
        degs = degs.head(3000)  # 限制数量为3000
        
        # 保存结果
        degs.to_csv(os.path.join(output_dir, f'cluster_{cluster}_deg.csv'), index=False)
        print(f"Differential expression genes for cluster {cluster} saved to {os.path.join(output_dir, f'cluster_{cluster}_deg.csv')}")

# 示例调用
data_path = r"D:\0-workingspace\key-marker\data\tabula_sapiens\ts_liver\test.h5ad"  # 输入数据路径
output_dir = r"D:\0-workingspace\key-marker\output\ts_liver"  # 输出目录

# 数据预处理和聚类
adata = preprocess_scRNAseq(data_path, output_dir)