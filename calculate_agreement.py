import pandas as pd
from sklearn.metrics import cohen_kappa_score, accuracy_score

def evaluate_agreement(annotator1_csv, annotator2_csv):
    df1 = pd.read_csv(annotator1_csv)
    df2 = pd.read_csv(annotator2_csv)
    
    # Ensure aligned rows
    merged = pd.merge(df1, df2, on='row_id', suffixes=('_a1', '_a2'))
    
    y1 = merged['category_a1']
    y2 = merged['category_a2']
    
    kappa = cohen_kappa_score(y1, y2)
    raw_acc = accuracy_score(y1, y2)
    disagreements = merged[merged['category_a1'] != merged['category_a2']]
    
    print(f"Raw Agreement: {raw_acc * 100:.2f}%")
    print(f"Cohen's Kappa: {kappa:.4f}")
    print(f"Total Disagreements: {len(disagreements)}")
    
    # Export disagreement list for manual resolution session
    disagreements.to_csv('disagreements_for_review.csv', index=False)

# Usage: evaluate_agreement('labels_member1.csv', 'labels_member2.csv')