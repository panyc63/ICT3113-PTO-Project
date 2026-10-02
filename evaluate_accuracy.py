import pandas as pd
import requests
from sklearn.metrics import classification_report, confusion_matrix

def run_accuracy_test(golden_csv_path, target_url):
    df = pd.read_csv(golden_csv_path)
    predictions = []
    
    for idx, row in df.iterrows():
        res = requests.post(target_url, json={"narrative": row['narrative']})
        pred_cat = res.json().get('category', 'Unknown')
        predictions.append(pred_cat)
        
    df['predicted'] = predictions
    
    print("--- CLASSIFICATION REPORT ---")
    print(classification_report(df['actual_category'], df['predicted']))
    
    print("--- CONFUSION MATRIX ---")
    print(confusion_matrix(df['actual_category'], df['predicted']))

# Usage: run_accuracy_test('golden_test_set.csv', 'http://localhost:8000/tickets')