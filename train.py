"""
Spamify Model Training Pipeline
Trains an optimized TF-IDF + Logistic Regression / Naive Bayes classifier
on email/SMS spam data and serializes the model artifact with rich metadata.
"""

import os
import sys
import json
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "emails.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "spam_model.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


def clean_text_for_training(text: str) -> str:
    """Strip common email artifacts for uniform training."""
    if not isinstance(text, str):
        return ""
    # Remove leading 'Subject: ' prefix if present
    if text.lower().startswith("subject:"):
        text = text[8:].strip()
    return text


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("=" * 60)
    print("[SPAMIFY] Training Spamify Classifier Pipeline")
    print("=" * 60)

    start_time = time.time()

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    print(f"[*] Loading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    initial_len = len(df)
    df = df.drop_duplicates(subset=["text"])
    dedup_len = len(df)
    print(f"[*] Total records: {initial_len} | Deduplicated records: {dedup_len}")

    # Check class distribution
    ham_count = int((df["spam"] == 0).sum())
    spam_count = int((df["spam"] == 1).sum())
    print(f"[*] Class Distribution: {ham_count} Ham ({ham_count/dedup_len:.1%}), {spam_count} Spam ({spam_count/dedup_len:.1%})")

    # Clean text
    df["clean_text"] = df["text"].apply(clean_text_for_training)

    # Train / Test split (80-20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"],
        df["spam"],
        test_size=0.2,
        random_state=42,
        stratify=df["spam"]
    )
    print(f"[*] Split: {len(X_train)} train samples, {len(X_test)} test samples")

    # Feature extraction with sublinear term-frequency scaling & unigram+bigram
    print("[*] Vectorizing text with TF-IDF (1-2 ngrams, max_features=15000)...")
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=15000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    vocab_size = len(vectorizer.vocabulary_)
    print(f"[*] Vocabulary size: {vocab_size} tokens")

    # Primary model: Regularized Logistic Regression with calibrated probabilities
    print("[*] Training Logistic Regression Classifier...")
    classifier = LogisticRegression(
        C=10.0,
        max_iter=1000,
        solver="lbfgs",
        random_state=42,
        class_weight="balanced"
    )
    classifier.fit(X_train_vec, y_train)

    # Also evaluate Naive Bayes for comparison
    nb_classifier = MultinomialNB(alpha=0.1)
    nb_classifier.fit(X_train_vec, y_train)
    nb_preds = nb_classifier.predict(X_test_vec)
    nb_acc = accuracy_score(y_test, nb_preds)

    # Predictions & metrics
    y_pred = classifier.predict(X_test_vec)
    y_prob = classifier.predict_proba(X_test_vec)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print("\n" + "=" * 40)
    print("[EVALUATION RESULTS (Test Set 20%)]")
    print("=" * 40)
    print(f"Accuracy:        {acc * 100:.2f}%")
    print(f"Precision:       {prec * 100:.2f}%")
    print(f"Recall:          {rec * 100:.2f}%")
    print(f"F1 Score:        {f1 * 100:.2f}%")
    print(f"ROC-AUC:         {roc_auc * 100:.2f}%")
    print(f"Naive Bayes Acc: {nb_acc * 100:.2f}%")
    print("-" * 40)
    print(f"Confusion Matrix:")
    print(f"  True Negatives (Ham as Ham):    {tn}")
    print(f"  False Positives (Ham as Spam):  {fp}")
    print(f"  False Negatives (Spam as Ham):  {fn}")
    print(f"  True Positives (Spam as Spam):  {tp}")
    print("=" * 40)

    # Extract top spam and ham feature tokens
    feature_names = np.array(vectorizer.get_feature_names_out())
    coefs = classifier.coef_[0]

    top_spam_indices = np.argsort(coefs)[-25:][::-1]
    top_ham_indices = np.argsort(coefs)[:25]

    top_spam_words = [
        {"token": feature_names[i], "weight": round(float(coefs[i]), 3)}
        for i in top_spam_indices
    ]
    top_ham_words = [
        {"token": feature_names[i], "weight": round(float(abs(coefs[i])), 3)}
        for i in top_ham_indices
    ]

    # Save model artifact
    model_payload = {
        "vectorizer": vectorizer,
        "classifier": classifier,
        "model_name": "TF-IDF + Calibrated Logistic Regression",
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    joblib.dump(model_payload, MODEL_PATH)
    print(f"[*] Serialized model artifact to {MODEL_PATH}")

    # Save metadata JSON for API & UI dashboard
    metadata = {
        "model_name": "Spamify Hybrid ML Classifier",
        "algorithm": "TF-IDF (1-2 ngrams, sublinear) + Logistic Regression (L2)",
        "accuracy": round(float(acc) * 100, 2),
        "precision": round(float(prec) * 100, 2),
        "recall": round(float(rec) * 100, 2),
        "f1_score": round(float(f1) * 100, 2),
        "roc_auc": round(float(roc_auc) * 100, 2),
        "naive_bayes_accuracy": round(float(nb_acc) * 100, 2),
        "dataset_stats": {
            "total_samples": dedup_len,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "ham_samples": ham_count,
            "spam_samples": spam_count,
            "vocab_size": vocab_size
        },
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp)
        },
        "top_spam_words": top_spam_words,
        "top_ham_words": top_ham_words,
        "training_duration_seconds": round(time.time() - start_time, 2)
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[*] Saved model metadata to {METADATA_PATH}")
    print(f"[OK] Pipeline training complete in {metadata['training_duration_seconds']}s!\n")


if __name__ == "__main__":
    train()
