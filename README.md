# 🛡️ Spamify AI - SMS & Email Spam Filtering Engine

> **State-of-the-Art Hybrid Spam, Phishing & Smishing Detection System** with **99.47% Accuracy**, **0.9998 ROC-AUC**, explainable threat keywords, rule-based heuristics, and an ultra-modern glassmorphic web dashboard.

---

## ✨ Features & Capabilities

- 🎯 **99.47% Test Accuracy & 99.98% ROC-AUC**:
  - Stratified 80/20 train/test evaluation across 5,695 deduplicated messages.
  - Sublinear TF-IDF (1-2 N-grams, 15,000 vocabulary) + Regularized Calibrated Logistic Regression.
  - Only 4 false positives and 2 false negatives out of 1,139 unseen test samples.

- ⚡ **Dual-Channel Protection (Email & SMS)**:
  - **Email Mode**: Inspects subject headers, body text, attachment references, and corporate/phishing cues.
  - **SMS Mode**: Specifically tuned for mobile smishing lures (package delivery scams, crypto giveaways, fake 2FA OTPs, bank urgent freezes, SMS segment counting).

- 🔍 **Explainable AI & Threat Attribution**:
  - Real-time extraction of top contributing trigger words (positive spam n-grams and negative ham words).
  - Interactive **X-Ray mode** highlighting suspicious keywords directly in the message text.
  - Heuristic security signals: detects IP-based links, URL shorteners (bit.ly, tinyurl), excessive uppercase shouting, and fear-urgency appeals.

- 🎨 **Modern Interactive Web Frontend**:
  - **Live Radial Risk Meter**: Dynamic SVG gauge animating from 0% to 100% spam risk with color transitions.
  - **1-Click Presets**: Realistic samples for instant testing (Meeting Notes, Bank Phishing Alert, USPS Delivery Scam, Crypto Prize, Friend SMS, Bank 2FA OTP).
  - **Batch & File Scanner**: Drag & drop `.csv` or `.txt` datasets or paste multi-line messages, with instant filterable tables and one-click CSV export.
  - **Model Analytics Tab**: Interactive charts of feature importance weights, test confusion matrix, and performance metrics.
  - **API Playground**: Live interactive code snippets for Python, JavaScript (`fetch`), and `cURL`.
  - **Dark & Light Mode**: Seamless glassmorphic theme with persistent preferences.

---

## 📁 Project Structure

```
Spamify-spam-filtering-for-SMS-and-Email/
├── app.py                            # Flask web application & REST API
├── spam_classifier.py                # Core hybrid ML + heuristics engine
├── train.py                          # Model training & serialization pipeline
├── emails.csv                        # Dataset (5,728 records)
├── email-spam-filter-improved.ipynb  # Clean, bug-free, fully documented Jupyter Notebook
├── email-spam-filter-99-03.ipynb     # Original legacy Kaggle notebook
├── requirements.txt                  # Python dependencies
├── run.bat                           # 1-Click Windows launch script
├── run.ps1                           # PowerShell launch script
├── models/
│   ├── spam_model.joblib             # Serialized vectorizer + calibrated model
│   └── model_metadata.json           # Model training metrics & top feature weights
└── templates/
    └── index.html                    # Modern Single-Page Application (SPA)
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train / Retrain Model (Optional)
The pre-trained model is already serialized in `models/spam_model.joblib`. To retrain:
```bash
python train.py
```

### 3. Launch the Web Application
```bash
python app.py
```
Or on Windows, simply double-click **`run.bat`** (or execute `.\run.ps1` in PowerShell)!

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📊 Model Evaluation Benchmarks

| Metric | Score | Note |
|---|---|---|
| **Accuracy** | **99.47%** | Top-tier binary classification |
| **Precision** | **98.55%** | Minimizes legitimate messages marked as spam |
| **Recall** | **99.27%** | Successfully catches 99.3% of malicious threats |
| **F1 Score** | **98.91%** | Harmonic mean of precision and recall |
| **ROC-AUC** | **99.98%** | Near-perfect probability separation |
| **Inference Latency** | **< 15 ms** | Real-time response |

### Confusion Matrix (Test Set: 1,139 samples)

| | Predicted HAM | Predicted SPAM |
|---|---|---|
| **Actual HAM (865)** | **861 (True Negatives)** | **4 (False Positives - 0.4%)** |
| **Actual SPAM (274)** | **2 (False Negatives - 0.7%)** | **272 (True Positives - 99.3%)** |

---

## 🔌 REST API Endpoints

### 1. Single Message Prediction
- **Endpoint**: `POST /api/predict`
- **Request Body**:
```json
{
  "text": "Your account has been locked. Verify immediately: http://bit.ly/bank-security",
  "subject": "Urgent Security Alert",
  "mode": "email"
}
```
- **Response**:
```json
{
  "classification": "SPAM",
  "risk_level": "HIGH_RISK",
  "risk_label": "High Risk Spam / Phishing",
  "spam_score": 85.2,
  "ham_score": 14.8,
  "trigger_words": [
    { "word": "account", "weight": 4.21, "impact": "Spam Indicator" },
    { "word": "click", "weight": 6.06, "impact": "Spam Indicator" }
  ],
  "heuristics": [
    {
      "type": "warning",
      "title": "URL Shortener Detected",
      "description": "Message masks destination using a shortened URL."
    }
  ],
  "recommendation": "Do not click on links or share personal credentials.",
  "latency_ms": 7.5
}
```

### 2. Bulk / Batch Prediction
- **Endpoint**: `POST /api/batch`
- **Payload**: Form data file upload (`.csv` or `.txt`), or JSON `{ "items": ["msg1", "msg2", ...] }`.
- Returns aggregate metrics (Spam Count, Ham Count, Average Threat Risk) and record-level predictions.

### 3. Model Information
- **Endpoint**: `GET /api/model-info`
- Returns training accuracy, dataset statistics, confusion matrix, and top feature weights.

---

## 📝 Jupyter Notebook Improvements

The newly added [`email-spam-filter-improved.ipynb`](email-spam-filter-improved.ipynb) resolves all issues in the original notebook:
- ✅ Added all missing imports (`pandas`, `numpy`, `sklearn`, `nltk`, `matplotlib`, `seaborn`).
- ✅ Replaced hardcoded Kaggle paths with dynamic local path detection.
- ✅ Fixed bug in original cell 54 where Decision Tree was called instead of Naive Bayes.
- ✅ Fixed variable overwriting bug in ROC-AUC calculation (cell 55).
- ✅ Benchmarked 5 machine learning models with side-by-side bar plots and confusion matrix heatmap.
