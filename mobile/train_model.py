"""
Model Training Script
Swahili Concern Classification System
Author: Obonyo Paul Rapando, 169688

Loads labelled_concerns.csv, generates AfroXLMR-large sentence embeddings,
balances classes with SMOTE if needed, trains an XGBoost classifier,
and saves the model + embedder reference for use by the classification module.

Run with: python scripts/train_model.py
"""

import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import joblib
import os

# Configuration
INPUT_FILE = 'data/processed/labelled_concerns.csv'
MODEL_DIR = 'models'
EMBEDDING_MODEL_NAME = 'Davlan/afro-xlmr-large'
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_data():
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} labelled sentences")
    print(df['label'].value_counts())
    return df


def embed_sentences(sentences, tokenizer, model, device, batch_size=16):
    """Generate mean-pooled AfroXLMR embeddings for a list of sentences."""
    embeddings = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            encoded = tokenizer(
                batch, padding=True, truncation=True,
                max_length=128, return_tensors='pt'
            ).to(device)
            output = model(**encoded)
            # Mean pooling over token embeddings, masking padding tokens
            token_embeddings = output.last_hidden_state
            mask = encoded['attention_mask'].unsqueeze(-1).expand(token_embeddings.size()).float()
            summed = torch.sum(token_embeddings * mask, dim=1)
            counts = torch.clamp(mask.sum(dim=1), min=1e-9)
            pooled = summed / counts
            embeddings.append(pooled.cpu().numpy())
            print(f"  Embedded {min(i + batch_size, len(sentences))}/{len(sentences)} sentences", end='\r')
    print()
    return np.vstack(embeddings)


def main():
    print("Starting model training pipeline...")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    df = load_data()

    print(f"\nLoading {EMBEDDING_MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
    model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME).to(device)

    print("\nGenerating embeddings...")
    X = embed_sentences(df['sentence'].tolist(), tokenizer, model, device)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df['label'])
    print(f"\nClasses: {list(label_encoder.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    # Check imbalance on the training set and apply SMOTE if needed
    class_counts = np.bincount(y_train)
    if class_counts.min() < class_counts.max() * 0.5:
        print("\nClass imbalance detected in training set — applying SMOTE")
        smote = SMOTE(random_state=RANDOM_STATE)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"After SMOTE: {len(X_train)} training samples")
        print(np.bincount(y_train))
    else:
        print("\nClass distribution acceptable — skipping SMOTE")

    print("\nTraining XGBoost classifier...")
    clf = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        objective='multi:softprob',
        num_class=len(label_encoder.classes_),
        random_state=RANDOM_STATE,
        eval_metric='mlogloss'
    )
    clf.fit(X_train, y_train)

    print("\nEvaluating on held-out test set...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, os.path.join(MODEL_DIR, 'xgboost_classifier.joblib'))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, 'label_encoder.joblib'))
    print(f"\nModel saved to {MODEL_DIR}/xgboost_classifier.joblib")
    print(f"Label encoder saved to {MODEL_DIR}/label_encoder.joblib")
    print(f"\nEmbedding model reference: {EMBEDDING_MODEL_NAME}")
    print("(loaded fresh at inference time in the classification module)")


if __name__ == '__main__':
    main()
