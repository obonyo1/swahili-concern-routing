"""
Data Preparation Script
Swahili Concern Classification System
Author: Obonyo Paul Rapando, 169688

Loads the Masasi and Masua (2024) Swahili Corpus, filters by domain,
and prepares a labelled CSV for XGBoost training.

Run with: python scripts/prepare_data.py
"""

import pandas as pd
import os

# Configuration
RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'
OUTPUT_FILE = 'data/processed/labelled_concerns.csv'

CATEGORY_FILES = {
    'Health':        'AFYA_Cleaned.txt',
    'Food Security': 'KILIMO_Cleaned.txt',
    'Shelter':       'NGO_Cleaned.txt',
    'Safety':        'MITANDAO_Cleaned.txt',
}

MIN_SENTENCE_LENGTH = 5
MAX_SENTENCE_LENGTH = 500


def load_and_label(filepath, label):
    """Load a text file and assign a category label to every line."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sentences = [line.strip() for line in lines if line.strip()]
    return pd.DataFrame({'sentence': sentences, 'label': label})


def clean_sentences(df):
    """Remove duplicates, very short lines, and very long lines."""
    initial_count = len(df)
    df = df.drop_duplicates(subset='sentence')
    df = df[df['sentence'].str.len() >= MIN_SENTENCE_LENGTH]
    df = df[df['sentence'].str.len() <= MAX_SENTENCE_LENGTH]
    df = df[~df['sentence'].str.match(r'^\d+$')]
    print(f"  Removed {initial_count - len(df)} rows during cleaning")
    return df


def main():
    print("Starting data preparation...")
    print(f"Reading corpus files from: {RAW_DIR}")
    all_dataframes = []

    for label, filename in CATEGORY_FILES.items():
        filepath = os.path.join(RAW_DIR, filename)

        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found. Skipping {label}.")
            continue

        print(f"\nLoading {label} from {filename}...")
        df = load_and_label(filepath, label)
        print(f"  Loaded {len(df)} sentences before cleaning")
        df = clean_sentences(df)
        print(f"  {len(df)} sentences after cleaning")
        all_dataframes.append(df)

    if not all_dataframes:
        print("ERROR: No corpus files found in data/raw/")
        print("Download the Masasi and Masua (2024) corpus from:")
        print("https://data.mendeley.com/datasets/d4yhn5b9n6/2")
        return

    dataset = pd.concat(all_dataframes, ignore_index=True)
    dataset = dataset.sample(frac=1, random_state=42).reset_index(drop=True)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    dataset.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

    print("\n" + "="*50)
    print("Dataset preparation complete.")
    print(f"Total samples:  {len(dataset)}")
    print("\nClass distribution:")
    print(dataset['label'].value_counts())
    print(f"\nSaved to: {OUTPUT_FILE}")

    min_count = dataset['label'].value_counts().min()
    max_count = dataset['label'].value_counts().max()
    if min_count < max_count * 0.5:
        print("\nWARNING: Class imbalance detected.")
        print("SMOTE will be applied during model training.")
    else:
        print("\nClass distribution is acceptable.")
    print("="*50)


if __name__ == '__main__':
    main()
