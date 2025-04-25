@echo off
setlocal enabledelayedexpansion

REM ========== 基础路径配置 ==========
set DATA_DIR=data/markers_human/exp_100
set OUTPUT_DIR=output/exp_100
set SOURCES_DIR=sources

REM ========== 1. 原始数据处理配置 ==========
set INPUT_DIR=%DATA_DIR%/llm_extract
set CM_INPUT_DIR=%DATA_DIR%/answer

REM ========== 2. marker标准化配置 ==========
set HGNC_FILE=%SOURCES_DIR%/hgnc_complete_set.txt
set GREEK_MAP_FILE=%SOURCES_DIR%/greek_map.json
set TS_STANDARD=%SOURCES_DIR%/tabula_sapiens/ts_standard.csv

REM ========== 3. 输出文件配置 ==========
REM 原始数据处理输出
set TOTAL_CSV=%OUTPUT_DIR%/total/total.csv
set GROUPED_TOTAL_CSV=%OUTPUT_DIR%/total/grouped_total.csv
set CM_TOTAL_CSV=%OUTPUT_DIR%/total/cm_total.csv
set CM_GROUPED_TOTAL_CSV=%OUTPUT_DIR%/total/cm_grouped_total.csv

REM ours marker标准化输出
set MYGENE_RESULTS=%OUTPUT_DIR%/marker/mygene_results.json
set MYGENE_STATUS=%OUTPUT_DIR%/marker/mygene_status.csv
set FALSE_MARKERS=%OUTPUT_DIR%/marker/false_markers.csv
set CORRECTED_MARKERS=%OUTPUT_DIR%/marker/corrected_markers.csv
set CORRECTED_TOTAL1=%OUTPUT_DIR%/marker/corrected_total.csv

REM CellMarker marker标准化输出
set CM_MYGENE_RESULTS=%OUTPUT_DIR%/marker/cm_mygene_results.json
set CM_MYGENE_STATUS=%OUTPUT_DIR%/marker/cm_mygene_status.csv
set CM_FALSE_MARKERS=%OUTPUT_DIR%/marker/cm_false_markers.csv
set CM_CORRECTED_MARKERS=%OUTPUT_DIR%/marker/cm_corrected_markers.csv
set CM_CORRECTED_TOTAL1=%OUTPUT_DIR%/marker/cm_corrected_total.csv

REM ours cell_tissue标准化输出
set MATCHED_TISSUE_CELL=%OUTPUT_DIR%/cell/matched_tissue_cell.csv
set FALSE_CELLS=%OUTPUT_DIR%/cell/false_cells.csv
set FILTER_TOTAL=%OUTPUT_DIR%/cell/filter_total.csv
set CORRECTED_TISSUE_CELL=%OUTPUT_DIR%/cell/corrected_tissue_cell.csv
set CORRECTED_TISSUE_CELL_EMB=%OUTPUT_DIR%/cell/corrected_tissue_cell_emb.csv
set FILTER_CORRECTED_TOTAL=%OUTPUT_DIR%/cell/filter_corrected_total.csv
set FILTER_CORRECTED_TOTAL_EMB=%OUTPUT_DIR%/cell/filter_corrected_total_emb.csv
set CORRECTED_TOTAL2=%OUTPUT_DIR%/cell/corrected_total.csv
set CORRECTED_TOTAL_EMB=%OUTPUT_DIR%/cell/corrected_total_emb.csv

REM CellMarker cell_tissue标准化输出
set CM_MATCHED_TISSUE_CELL=%OUTPUT_DIR%/cell/cm_matched_tissue_cell.csv
set CM_FALSE_CELLS=%OUTPUT_DIR%/cell/cm_false_cells.csv
set CM_FILTER_TOTAL=%OUTPUT_DIR%/cell/cm_filter_total.csv
set CM_CORRECTED_TISSUE_CELL=%OUTPUT_DIR%/cell/cm_corrected_tissue_cell.csv
set CM_CORRECTED_TISSUE_CELL_EMB=%OUTPUT_DIR%/cell/cm_corrected_tissue_cell_emb.csv
set CM_FILTER_CORRECTED_TOTAL=%OUTPUT_DIR%/cell/cm_filter_corrected_total.csv
set CM_FILTER_CORRECTED_TOTAL_EMB=%OUTPUT_DIR%/cell/cm_filter_corrected_total_emb.csv
set CM_CORRECTED_TOTAL2=%OUTPUT_DIR%/cell/cm_corrected_total.csv
set CM_CORRECTED_TOTAL_EMB=%OUTPUT_DIR%/cell/cm_corrected_total_emb.csv

REM 评估结果
set BEFORE_MARKER_RESULT_CSV=%OUTPUT_DIR%/marker/before_result.csv
set AFTER_MARKER_RESULT_CSV=%OUTPUT_DIR%/marker/after_result.csv
set BEFORE_CELL_RESULT_CSV=%OUTPUT_DIR%/cell/before_result.csv
set BEFORE_FILTER_RESULT_CSV=%OUTPUT_DIR%/cell/before_filter_result.csv
set AFTER_CELL_RESULT_CSV=%OUTPUT_DIR%/cell/after_result.csv
set AFTER_FILTER_RESULT_CSV=%OUTPUT_DIR%/cell/after_filter_result.csv


REM ========== 执行流程 ==========
REM 1. 原始数据处理
@REM 1.utils/1_marker_process.py文件处理爬取到的x篇文章的数据，得到total.csv和group.csv文件，output_file记录了所有文章的marker信息，grouped_output_file文件记录了按照文章分组的marker信息。
echo Step 1: Processing raw data...
python utils/1_marker_process.py --input_dir !INPUT_DIR! --output_file !TOTAL_CSV! --grouped_output_file !GROUPED_TOTAL_CSV!
python utils/1_marker_process.py --input_dir !CM_INPUT_DIR! --output_file !CM_TOTAL_CSV! --grouped_output_file !CM_GROUPED_TOTAL_CSV!

REM 2. marker标准化
@REM 2.1 MyGene查询，得到mygene_results.json文件，mygene_status.csv文件记录了每个marker的查询结果，false_markers.csv文件记录了查询失败的marker。
echo Step 2.1: Marker standardization...
REM 2.1 MyGene查询
python utils/2_mygene_query.py --file_path !TOTAL_CSV! --json_output !MYGENE_RESULTS! --csv_output !MYGENE_STATUS! --false_markers !FALSE_MARKERS!
python utils/2_mygene_query.py --file_path !CM_TOTAL_CSV! --json_output !CM_MYGENE_RESULTS! --csv_output !CM_MYGENE_STATUS! --false_markers !CM_FALSE_MARKERS!

REM 2.2 marker校正
@REM 2.2 marker校正, 包括marker预处理、tf/idf检索还有大模型调用。最后得到corrected_markers.csv，记录了标准化前后的marker名。
echo Step 2.2: Marker correction...
python utils/marker_correct/1_correct_markers.py --hgnc_file !HGNC_FILE! --false_markers !FALSE_MARKERS! --greek_map !GREEK_MAP_FILE! --output !CORRECTED_MARKERS!
python utils/marker_correct/1_correct_markers.py --hgnc_file !HGNC_FILE! --false_markers !CM_FALSE_MARKERS! --greek_map !GREEK_MAP_FILE! --output !CM_CORRECTED_MARKERS!

REM 2.3 更新total.csv
@REM 2.3 更新total.csv，将corrected_markers.csv中的marker名替换到total.csv中,得到corrected_total.csv文件。
echo Step 2.3: Updating total.csv...
python utils/marker_correct/2_correct_total.py --total_csv !TOTAL_CSV! --corrected_markers !CORRECTED_MARKERS! --output  !CORRECTED_TOTAL1!
python utils/marker_correct/2_correct_total.py --total_csv !CM_TOTAL_CSV! --corrected_markers !CM_CORRECTED_MARKERS! --output !CM_CORRECTED_TOTAL1!

REM 3. marker标准化评估
echo Step 3: Marker Evaluation...
python utils/3_eval.py --cm_path !CM_CORRECTED_TOTAL1! --test_path !CORRECTED_TOTAL1! --output !AFTER_MARKER_RESULT_CSV!
python utils/3_eval.py --cm_path !CM_TOTAL_CSV! --test_path !TOTAL_CSV! --output !BEFORE_MARKER_RESULT_CSV!

REM 4. cell_tissue标准化
@REM 细胞组织匹配, 包括细胞组织匹配和过滤。最后得到matched_tissue_cell.csv文件，记录了匹配到的细胞组织，false_cells.csv文件记录了匹配失败的细胞组织，filter_total.csv文件记录了过滤后的数据。
echo Step 4: Cell tissue standardization...
echo ours
python utils/cell_correct/1_cell_tissue_match.py --ts_standard !TS_STANDARD! --corrected_total !CORRECTED_TOTAL1! --matched_output !MATCHED_TISSUE_CELL! --false_output !FALSE_CELLS! --filter_output !FILTER_TOTAL!
echo CellMarker
python utils/cell_correct/1_cell_tissue_match.py --ts_standard !TS_STANDARD! --corrected_total !CM_CORRECTED_TOTAL1! --matched_output !CM_MATCHED_TISSUE_CELL! --false_output !CM_FALSE_CELLS! --filter_output !CM_FILTER_TOTAL!

REM 5. 使用大模型标准化cell_tissue
@REM 这个代码是使用tf-idf检索信息之后再交给大模型标准化。后面我又改了一下，首先使用utils/cell_correct/search_standard_v2.py来进行向量化和信息检索，检索出来的结果保存在memory里，然后使用utils/cell_correct/2_correct_cells_v2.py读取检索结果，交给大模型进行标准化。
@REM 最终得到的是corrected_tissue_cell.csv文件，记录了标准化后的细胞组织。
echo Step 5: LLM-based cell_tissue standardization...
echo ours
python utils/cell_correct/2_correct_cells.py --input_false_cells !FALSE_CELLS! --ts_standard !TS_STANDARD! --output !CORRECTED_TISSUE_CELL!
echo CellMarker
python utils/cell_correct/2_correct_cells.py --input_false_cells !CM_FALSE_CELLS! --ts_standard !TS_STANDARD! --output !CM_CORRECTED_TISSUE_CELL!

REM 6. 修正total.csv
@REM 利用上一步得到的corrected_tissue_cell.csv文件，修正total.csv文件，得到corrected_total.csv文件。
echo Step 6: correcting total.csv...
echo ours
python utils/cell_correct/3_correct_total.py --cell_tissue_corrected !CORRECTED_TISSUE_CELL_EMB! --filter_path !FILTER_TOTAL! --marker_total !CORRECTED_TOTAL1! --filter_corrected !FILTER_CORRECTED_TOTAL_EMB! --corrected !CORRECTED_TOTAL_EMB!
echo CellMarker
python utils/cell_correct/3_correct_total.py --cell_tissue_corrected !CM_CORRECTED_TISSUE_CELL_EMB! --filter_path !CM_FILTER_TOTAL! --marker_total !CM_CORRECTED_TOTAL1! --filter_corrected !CM_FILTER_CORRECTED_TOTAL_EMB! --corrected !CM_CORRECTED_TOTAL_EMB!

REM 7. cell tissue标准化评估
echo Step 7: Evaluating cell_tissue standardization...
REM 7.1 过滤前数据的评估
echo total before
python utils/3_eval.py --cm_path !CM_CORRECTED_TOTAL1! --test_path !CORRECTED_TOTAL1! --output !BEFORE_CELL_RESULT_CSV!
echo total after(tfidf)
python utils/3_eval.py --cm_path !CM_CORRECTED_TOTAL2! --test_path !CORRECTED_TOTAL2! --output !AFTER_CELL_RESULT_CSV!
echo total after(emb)
python utils/3_eval.py --cm_path !CM_CORRECTED_TOTAL_EMB! --test_path !CORRECTED_TOTAL_EMB! --output !AFTER_CELL_RESULT_CSV!

REM 7.2 过滤后数据的评估
echo filter before
python utils/3_eval.py --cm_path !CM_FILTER_TOTAL! --test_path !FILTER_TOTAL! --output !BEFORE_FILTER_RESULT_CSV!
echo filter after(tfidf)
python utils/3_eval.py --cm_path !CM_FILTER_CORRECTED_TOTAL! --test_path !FILTER_CORRECTED_TOTAL! --output !AFTER_FILTER_RESULT_CSV!
echo filter after(emb)
python utils/3_eval.py --cm_path !CM_FILTER_CORRECTED_TOTAL_EMB! --test_path !FILTER_CORRECTED_TOTAL_EMB! --output !AFTER_FILTER_RESULT_CSV!

echo All steps completed!