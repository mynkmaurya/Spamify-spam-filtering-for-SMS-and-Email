"""
Spamify Core Classifier Engine
Hybrid Machine Learning (TF-IDF + Logistic Regression) + Rule-Based Heuristics
Specialized for both Email and SMS messages.
"""

import os
import re
import html
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "spam_model.joblib")

# Common phishing and scam regex patterns
URL_REGEX = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
IP_URL_REGEX = re.compile(r"https?://(?:\d{1,3}\.){3}\d{1,3}(?:[^\s<>\"']*)", re.IGNORECASE)
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bit.do", "cutt.ly", "shorturl.at"
}

PHISHING_KEYWORDS = [
    "account suspended", "action required", "verify your account", "verify identity",
    "unauthorized transaction", "security alert", "suspicious activity", "banking alert",
    "wire transfer", "western union", "cryptocurrency", "bitcoin", "claim your prize",
    "lottery winner", "winner selected", "urgent notice", "reset your password immediately",
    "tax refund", "irs notice", "package delivery failed", "usps notice", "click here to claim",
    "risk of closure", "inheritance claim", "confidential proposal", "earn extra cash"
]

SMS_SPECIFIC_SCAMS = [
    "delivery attempted", "re-schedule delivery", "unclaimed package",
    "gift card waiting", "card locked", "otp will expire", "reply stop to unsubscribe"
]


class SpamifyEngine:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.vectorizer = None
        self.classifier = None
        self.vocab = None
        self.coefs = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                payload = joblib.load(self.model_path)
                self.vectorizer = payload["vectorizer"]
                self.classifier = payload["classifier"]
                self.vocab = np.array(self.vectorizer.get_feature_names_out())
                self.coefs = self.classifier.coef_[0]
                self.feature_weight_map = dict(zip(self.vocab, self.coefs))
                self.is_loaded = True
                print(f"[SpamifyEngine] Loaded trained model from {self.model_path}")
            except Exception as e:
                print(f"[SpamifyEngine] Error loading model: {e}")
                self.is_loaded = False
        else:
            print(f"[SpamifyEngine] Warning: Model artifact not found at {self.model_path}. Please run train.py first.")

    def extract_heuristics(self, text: str, mode: str = "email"):
        """Extract rule-based risk indicators from raw text."""
        alerts = []
        heuristic_score = 0.0
        lower_text = text.lower()

        # 1. URL Analysis
        urls = URL_REGEX.findall(text)
        has_ip_url = bool(IP_URL_REGEX.search(text))
        has_shortener = False

        for url in urls:
            for shortener in SHORTENER_DOMAINS:
                if shortener in url.lower():
                    has_shortener = True
                    break

        if has_ip_url:
            alerts.append({
                "type": "danger",
                "title": "Raw IP Address URL",
                "description": "Email contains link with a numerical IP address instead of a recognized domain."
            })
            heuristic_score += 0.35

        if has_shortener:
            alerts.append({
                "type": "warning",
                "title": "URL Shortener Detected",
                "description": "Message masks the final destination using a shortened URL (e.g. bit.ly, tinyurl)."
            })
            heuristic_score += 0.25

        if len(urls) > 3:
            alerts.append({
                "type": "info",
                "title": "Multiple External Links",
                "description": f"Contains {len(urls)} external links."
            })
            heuristic_score += 0.10

        # 2. Phishing & Fear Urgency Phrases
        matched_phrases = []
        for phrase in PHISHING_KEYWORDS:
            if phrase in lower_text:
                matched_phrases.append(phrase)

        if mode == "sms":
            for phrase in SMS_SPECIFIC_SCAMS:
                if phrase in lower_text and phrase not in matched_phrases:
                    matched_phrases.append(phrase)

        if matched_phrases:
            alerts.append({
                "type": "danger" if len(matched_phrases) >= 2 else "warning",
                "title": "Phishing / Urgency Phrases",
                "description": f"Detected high-risk trigger phrases: {', '.join(matched_phrases[:3])}."
            })
            heuristic_score += min(0.40, len(matched_phrases) * 0.15)

        # 3. Capitalization & Punctuation
        letters = [c for c in text if c.isalpha()]
        if len(letters) > 15:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio > 0.45:
                alerts.append({
                    "type": "warning",
                    "title": "Excessive Capitalization",
                    "description": f"{int(upper_ratio * 100)}% of letters are UPPERCASE, typical of urgent spam lures."
                })
                heuristic_score += 0.15

        exclamations = text.count("!")
        if exclamations >= 4:
            alerts.append({
                "type": "info",
                "title": "High Exclamation Intensity",
                "description": f"Contains {exclamations} exclamation marks."
            })
            heuristic_score += 0.05

        # 4. Currency / Money Symbols
        currency_count = sum(text.count(sym) for sym in ["$", "€", "£", "₹"])
        if currency_count >= 3:
            alerts.append({
                "type": "info",
                "title": "Frequent Currency Symbols",
                "description": "Multiple references to cash, currency, or payments."
            })
            heuristic_score += 0.10

        return alerts, min(heuristic_score, 0.70)

    def find_trigger_words(self, text: str, max_words: int = 10):
        """Identify which words in the text most strongly swayed the model."""
        if not self.is_loaded:
            return []

        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        found_triggers = []
        seen = set()

        # Check unigrams and bigrams
        tokens_to_check = []
        for w in words:
            tokens_to_check.append(w)
        for i in range(len(words) - 1):
            tokens_to_check.append(f"{words[i]} {words[i+1]}")

        for token in tokens_to_check:
            if token in seen:
                continue
            weight = self.feature_weight_map.get(token)
            if weight is not None:
                seen.add(token)
                category = "spam" if weight > 0 else "ham"
                found_triggers.append({
                    "word": token,
                    "weight": round(float(weight), 2),
                    "impact": "Spam Indicator" if weight > 0 else "Safe Indicator",
                    "category": category
                })

        # Sort: spam indicators first by weight descending, then ham indicators
        found_triggers.sort(key=lambda x: abs(x["weight"]), reverse=True)
        return found_triggers[:max_words]

    def build_highlighted_html(self, text: str, triggers: list) -> str:
        """Render text with safe HTML span highlights for detected trigger words."""
        safe_text = html.escape(text)

        # Collect spam trigger words
        spam_words = [t["word"] for t in triggers if t["category"] == "spam" and t["weight"] > 0.5]
        spam_words.sort(key=len, reverse=True)

        for w in spam_words:
            # Highlight with a regex that preserves original casing
            pattern = re.compile(rf"\b({re.escape(w)})\b", re.IGNORECASE)
            safe_text = pattern.sub(
                r'<mark class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/40" title="Spam Indicator: \1">\1</mark>',
                safe_text
            )

        # Highlight URLs
        url_pattern = re.compile(r"(https?://[^\s<>\"']+|www\.[^\s<>\"']+)", re.IGNORECASE)
        safe_text = url_pattern.sub(
            r'<span class="text-amber-300 underline font-mono text-xs bg-amber-500/10 px-1 py-0.5 rounded" title="Detected Link">\1</span>',
            safe_text
        )

        return safe_text

    def predict(self, text: str, subject: str = "", mode: str = "email") -> dict:
        """
        Analyze an email or SMS message and return comprehensive classification.
        """
        if not self.is_loaded:
            # Try to load if newly generated
            self._load_model()
            if not self.is_loaded:
                return {
                    "error": "Model is not trained yet. Please run train.py first."
                }

        # Combine subject and body if provided
        full_text = text.strip()
        if subject.strip():
            full_text = f"Subject: {subject.strip()}\n\n{full_text}"

        # Clean text
        clean_text = full_text
        if clean_text.lower().startswith("subject:"):
            clean_text = clean_text[8:].strip()

        # Word & Char counts
        char_count = len(full_text)
        words = full_text.split()
        word_count = len(words)

        # ML Prediction
        vec = self.vectorizer.transform([clean_text])
        ml_prob_spam = float(self.classifier.predict_proba(vec)[0][1])
        ml_prob_ham = float(1.0 - ml_prob_spam)

        # Heuristic Analysis
        heuristics, heuristic_boost = self.extract_heuristics(full_text, mode=mode)

        # Hybrid Spam Score Calculation (0 to 100)
        # Combine ML probability with rule-based heuristics
        if heuristic_boost > 0:
            combined_spam_prob = min(0.999, ml_prob_spam * 0.75 + heuristic_boost * 0.40)
        else:
            combined_spam_prob = ml_prob_spam

        spam_score_pct = round(combined_spam_prob * 100, 1)
        ham_score_pct = round((1.0 - combined_spam_prob) * 100, 1)

        # Classification label & Risk Tier
        if spam_score_pct >= 65.0:
            classification = "SPAM"
            risk_level = "HIGH_RISK"
            risk_label = "High Risk Spam / Phishing"
            badge_color = "danger"
            recommendation = (
                "Do not click on any links, do not download attachments, and never "
                "provide personal credentials, OTPs, or financial information."
            )
        elif spam_score_pct >= 35.0:
            classification = "SUSPICIOUS"
            risk_level = "SUSPICIOUS"
            risk_label = "Suspicious / Promotional"
            badge_color = "warning"
            recommendation = (
                "This message exhibits characteristics of marketing or unsolicited outreach. "
                "Verify the sender's identity before interacting."
            )
        else:
            classification = "HAM"
            risk_level = "SAFE"
            risk_label = "Safe / Legitimate Message"
            badge_color = "success"
            recommendation = "No malicious patterns or high-risk spam signals detected. Appears safe."

        # Trigger Words
        triggers = self.find_trigger_words(clean_text, max_words=8)
        highlighted_html = self.build_highlighted_html(full_text, triggers)

        return {
            "classification": classification,
            "risk_level": risk_level,
            "risk_label": risk_label,
            "badge_color": badge_color,
            "spam_score": spam_score_pct,
            "ham_score": ham_score_pct,
            "ml_confidence": {
                "spam_probability": round(ml_prob_spam * 100, 2),
                "ham_probability": round(ml_prob_ham * 100, 2),
            },
            "heuristics": heuristics,
            "trigger_words": triggers,
            "recommendation": recommendation,
            "highlighted_html": highlighted_html,
            "metadata": {
                "mode": mode,
                "character_count": char_count,
                "word_count": word_count,
                "has_subject": bool(subject.strip())
            }
        }


# Singleton engine instance
engine = SpamifyEngine()
