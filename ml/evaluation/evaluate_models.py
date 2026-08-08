"""Evaluates any saved models and prints a consolidated report.

Usage: python ml/evaluation/evaluate_models.py
"""
import os, json, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "models", "*_metrics.json")))
    if not files:
        print("No trained models found. Run the scripts in ml/training/ first.")
        return
    for f in files:
        print(f"\n=== {os.path.basename(f).replace('_metrics.json','')} ===")
        print(json.dumps(json.load(open(f)), indent=2))

if __name__ == "__main__":
    main()
