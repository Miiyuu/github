# 基础路径配置
DATA_DIR = "data/markers_human/exp_3_2"
OUTPUT_DIR = "output/exp_3_2"
SOURCES_DIR = "sources"

# 1. 原始数据处理配置
INPUT_DIR = f"{DATA_DIR}/llm_extract"
CM_INPUT_DIR = f"{DATA_DIR}/answer"

# 2. marker标准化配置
HGNC_FILE = f"{SOURCES_DIR}/hgnc_complete_set.txt"
GREEK_MAP_FILE = f"{SOURCES_DIR}/greek_map.json"
TS_STANDARD = f"{SOURCES_DIR}/tabula_sapiens/ts_standard.csv"

# 3. 输出文件配置
class OutputFiles:
    # 原始数据处理输出
    TOTAL_CSV = f"{OUTPUT_DIR}/total/total.csv"
    GROUPED_TOTAL_CSV = f"{OUTPUT_DIR}/total/grouped_total.csv"
    CM_TOTAL_CSV = f"{OUTPUT_DIR}/total/cm_total.csv"
    CM_GROUPED_TOTAL_CSV = f"{OUTPUT_DIR}/total/cm_grouped_total.csv"
    
    # marker标准化输出
    MYGENE_RESULTS = f"{OUTPUT_DIR}/marker/mygene_results.json"
    MYGENE_STATUS = f"{OUTPUT_DIR}/marker/mygene_status.csv"
    FALSE_MARKERS = f"{OUTPUT_DIR}/marker/false_markers.csv"
    CORRECTED_MARKERS = f"{OUTPUT_DIR}/marker/corrected_markers.csv"
    CORRECTED_TOTAL = f"{OUTPUT_DIR}/marker/corrected_total.csv"
    
    # CellMarker标准化输出
    CM_MYGENE_RESULTS = f"{OUTPUT_DIR}/marker/cm_mygene_results.json"
    CM_MYGENE_STATUS = f"{OUTPUT_DIR}/marker/cm_mygene_status.csv"
    CM_FALSE_MARKERS = f"{OUTPUT_DIR}/marker/cm_false_markers.csv"
    CM_CORRECTED_MARKERS = f"{OUTPUT_DIR}/marker/cm_corrected_markers.csv"
    CM_CORRECTED_TOTAL = f"{OUTPUT_DIR}/marker/cm_corrected_total.csv"
    
    # cell_tissue标准化输出
    MATCHED_TISSUE_CELL = f"{OUTPUT_DIR}/cell/matched_tissue_cell.csv"
    FALSE_CELLS = f"{OUTPUT_DIR}/cell/false_cells.csv"
    FILTER_TOTAL = f"{OUTPUT_DIR}/cell/filter_total.csv"
    CORRECTED_TISSUE_CELL = f"{OUTPUT_DIR}/cell/corrected_tissue_cell.csv"
    FILTER_CORRECTED_TOTAL = f"{OUTPUT_DIR}/cell/filter_corrected_total.csv"
    
    # CellMarker cell_tissue标准化输出
    CM_MATCHED_TISSUE_CELL = f"{OUTPUT_DIR}/cell/cm_matched_tissue_cell.csv"
    CM_FALSE_CELLS = f"{OUTPUT_DIR}/cell/cm_false_cells.csv"
    CM_FILTER_TOTAL = f"{OUTPUT_DIR}/cell/cm_filter_total.csv"
    CM_CORRECTED_TISSUE_CELL = f"{OUTPUT_DIR}/cell/cm_corrected_tissue_cell.csv"
    CM_FILTER_CORRECTED_TOTAL = f"{OUTPUT_DIR}/cell/cm_filter_corrected_total.csv"
    
    # 评估结果
    RESULT_CSV = f"{OUTPUT_DIR}/marker/result.csv"
    FILTER_RESULT_CSV = f"{OUTPUT_DIR}/marker/filter_result.csv"