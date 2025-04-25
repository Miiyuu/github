import anndata

adata = anndata.read_h5ad(r'D:\0-workingspace\key-marker\data\tabula_sapiens\ts_liver\valid.h5ad')
print(adata.obs['cell_ontology_class'].unique())
print(adata.obs['free_annotation'].unique())
print(adata.obs['organ_tissue'].unique())
