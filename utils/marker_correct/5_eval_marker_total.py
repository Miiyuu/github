import pandas as pd
import os
from pathlib import Path

# Define file paths
total_csv_path = r"data\markers_human\exp_3\total.csv"
ground_truth_path = r"data\markers_human\exp_3\answer\cm_total.csv"
results_path = r"output\exp_100\marker\marker_eval_results_total_ori.csv"

# Step 1: Read total.csv (our extracted markers)
total_df = pd.read_csv(total_csv_path)

# Step 2: Read ground truth data
merged_df = pd.read_csv(ground_truth_path)

# Get all unique markers from both datasets (ignoring PMIDs)
our_markers = set(total_df['marker'].unique())
true_markers = set(merged_df['marker'].unique())

# Calculate overall metrics
tp = len(our_markers & true_markers)  # True positives
fp = len(our_markers - true_markers)  # False positives
fn = len(true_markers - our_markers)  # False negatives

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0

# Create results DataFrame
results_df = pd.DataFrame([{
    'precision': precision,
    'recall': recall,
    'true_markers_count': len(true_markers),
    'extracted_markers_count': len(our_markers),
    'true_positives': tp,
    'false_positives': fp,
    'false_negatives': fn
}])

# Save results
results_df.to_csv(results_path, index=False)

# Print summary
print("\nEvaluation Results Summary:")
print(f"Overall Precision: {precision:.4f}")
print(f"Overall Recall: {recall:.4f}")
print(f"True Positives: {tp}")
print(f"False Positives: {fp}")
print(f"False Negatives: {fn}")
print(f"\nResults saved to: {results_path}")

# Show results
print("\nResults:")
print(results_df)