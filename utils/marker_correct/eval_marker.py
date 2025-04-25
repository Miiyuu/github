import pandas as pd
import os
from pathlib import Path

# Define file paths
# total_csv_path = r"D:\0-workingspace\key-marker\data\markers_human\exp_100\llm_extract_100\total.csv"
total_csv_path = r"D:\0-workingspace\key-marker\output\exp_3\marker\corrected_total_0409.csv"
cellmarker_dir = r"D:\0-workingspace\key-marker\data\markers_human\exp_3\answer"
output_path = r"D:\0-workingspace\key-marker\data\markers_human\exp_3\merged_ori.csv"
results_path = r"D:\0-workingspace\key-marker\output\exp_3\marker\marker_eval_results_new.csv"

# Step 1: Read total.csv
total_df = pd.read_csv(total_csv_path)

# Get unique PMIDs from total.csv
pmids_in_total = total_df['pmid'].unique()

# Step 2: Find and merge all {pmid}.xlsx files from cellmarker_answer_100
merged_data = []

for pmid in pmids_in_total:
    xlsx_path = os.path.join(cellmarker_dir, f"{pmid}.xlsx")
    if os.path.exists(xlsx_path):
        df = pd.read_excel(xlsx_path)
        df['pmid'] = pmid  # Add pmid column for reference
        merged_data.append(df)

# Combine all xlsx files into one DataFrame
if merged_data:
    merged_df = pd.concat(merged_data, ignore_index=True)
    # Save merged data
    merged_df.to_csv(output_path, index=False)
else:
    print("No matching xlsx files found in the directory.")
    exit()

# Step 3: Calculate recall and precision for each PMID
results = []

for pmid in pmids_in_total:
    # Get markers from total.csv (our extraction)
    our_markers = set(total_df[total_df['pmid'] == pmid]['marker'].unique())
    
    # Get markers from merged_df (ground truth)
    true_markers = set(merged_df[merged_df['pmid'] == pmid]['marker'].unique())
    
    # Calculate metrics
    if true_markers:  # Only calculate if there are ground truth markers
        tp = len(our_markers & true_markers)  # True positives
        fp = len(our_markers - true_markers)  # False positives
        fn = len(true_markers - our_markers)  # False negatives
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        results.append({
            'pmid': pmid,
            'precision': precision,
            'recall': recall,
            'true_markers_count': len(true_markers),
            'extracted_markers_count': len(our_markers),
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn
        })

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Calculate averages
avg_precision = results_df['precision'].mean()
avg_recall = results_df['recall'].mean()

# Calculate totals across all PMIDs (combined metrics)
total_tp = results_df['true_positives'].sum()
total_fp = results_df['false_positives'].sum()
total_fn = results_df['false_negatives'].sum()

total_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
total_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0

# Add summary row (average metrics) and total row (combined metrics)
summary_row = pd.DataFrame([{
    'pmid': 'Average',
    'precision': avg_precision,
    'recall': avg_recall,
    'true_markers_count': results_df['true_markers_count'].sum(),
    'extracted_markers_count': results_df['extracted_markers_count'].sum(),
    'true_positives': results_df['true_positives'].sum(),
    'false_positives': results_df['false_positives'].sum(),
    'false_negatives': results_df['false_negatives'].sum()
}])

total_row = pd.DataFrame([{
    'pmid': 'Total',
    'precision': total_precision,
    'recall': total_recall,
    'true_markers_count': results_df['true_markers_count'].sum(),
    'extracted_markers_count': results_df['extracted_markers_count'].sum(),
    'true_positives': total_tp,
    'false_positives': total_fp,
    'false_negatives': total_fn
}])

results_df = pd.concat([results_df, summary_row, total_row], ignore_index=True)

# Save results
results_df.to_csv(results_path, index=False)

# Print summary
print("\nEvaluation Results Summary:")
print(f"Average Precision across all PMIDs: {avg_precision:.4f}")
print(f"Average Recall across all PMIDs: {avg_recall:.4f}")
print(f"\nDetailed results saved to: {results_path}")
print(f"Merged ground truth data saved to: {output_path}")

# Show top 5 rows of results
print("\nSample of results:")
print(results_df.head())