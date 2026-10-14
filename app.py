"""
Spamify Web Application & REST API
High-performance spam detection web server with interactive modern UI.
"""

import os
import sys
import json
import csv
import io
import time
from flask import Flask, render_template, request, jsonify

# Windows stdout utf-8 setup
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from spam_classifier import engine

app = Flask(__name__, template_folder="templates", static_folder="static")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")

# Predefined realistic examples for quick 1-click testing
CURATED_EXAMPLES = [
    {
        "id": "ex_email_ham_1",
        "category": "ham",
        "type": "email",
        "title": "Quarterly Project Review",
        "badge": "Safe Email",
        "subject": "Sprint planning and Q4 project deliverable review",
        "text": "Hi team,\n\nI hope you are having a productive week. Please review the attached sprint retrospective notes before our 2:00 PM synchronization meeting tomorrow.\n\nKey discussion items:\n- Review of user feedback on the analytics dashboard\n- Finalizing API integration milestones\n- Infrastructure migration schedule\n\nPlease let me know if you would like to add any items to the agenda.\n\nBest regards,\nDavid Miller\nProduct Engineering Team"
    },
    {
        "id": "ex_email_spam_1",
        "category": "spam",
        "type": "email",
        "title": "Urgent Bank Security Alert",
        "badge": "Phishing Email",
        "subject": "CRITICAL: Unauthorized attempt detected on your bank account!",
        "text": "Dear Valued Customer,\n\nWe detected an unauthorized sign-in attempt to your online banking portal from an unrecognized IP address (194.26.29.11).\n\nFor your protection, your access has been temporarily suspended. You must verify your credentials within 24 hours to prevent permanent account suspension.\n\n>> CLICK HERE TO VERIFY YOUR IDENTITY NOW: http://bit.ly/secure-account-verification-auth\n\nFailure to confirm your details will result in your funds being restricted.\n\nFraud Prevention Center\nGlobal Trust Financial"
    },
    {
        "id": "ex_email_spam_2",
        "category": "spam",
        "type": "email",
        "title": "Lottery & Inheritance Claim",
        "badge": "Financial Scam",
        "subject": "CONFIDENTIAL PROPOSAL: Transfer of $14,500,000 USD Unclaimed Funds",
        "text": "Attn: Beneficiary,\n\nI am contacting you regarding a dormant estate account holding $14,500,000 USD left by a deceased client with your identical surname. As the legal trustee, I am prepared to transfer 40% of this fund to your account as the official next-of-kin.\n\nThis transaction is 100% risk-free. Reply immediately with your full legal name, private telephone number, and banking details to initiate the swift wire transfer.\n\nConfidentiality is guaranteed.\nBarrister Patrick Vance, Esq."
    },
    {
        "id": "ex_sms_scam_1",
        "category": "spam",
        "type": "sms",
        "title": "USPS Package Delivery Smishing",
        "badge": "Scam SMS",
        "subject": "",
        "text": "[USPS Notification]: Your package USPS-9382103 cannot be delivered due to an incomplete street address. Please update your delivery preference and pay $1.99 redelivery fee within 12 hours: http://192.168.1.45/usps-track"
    },
    {
        "id": "ex_sms_scam_2",
        "category": "spam",
        "type": "sms",
        "title": "Crypto / Prize Giveaway",
        "badge": "Prize Scam",
        "subject": "",
        "text": "CONGRATULATIONS! Your mobile number was selected as the 1st prize winner of 0.75 Bitcoin ($48,000). Claim your reward code [BTC-8899] before midnight at http://bit.ly/claim-btc-prize or call 1-800-CLAIM-NOW!"
    },
    {
        "id": "ex_sms_ham_1",
        "category": "ham",
        "type": "sms",
        "title": "Friend Dinner Plan",
        "badge": "Safe SMS",
        "subject": "",
        "text": "Hey Alex! Are we still on for Italian dinner tonight at 7:30? Let me know if you want me to reserve a table, see you soon!"
    },
    {
        "id": "ex_sms_ham_2",
        "category": "ham",
        "type": "sms",
        "title": "Bank 2FA Security Code",
        "badge": "2FA OTP",
        "subject": "",
        "text": "Chase Security: 849204 is your temporary one-time passcode for online access. Never share this code with anyone. We will never call to request this code."
    }
]


@app.route("/")
def index():
    """Serve the modern SPA frontend."""
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """Single message spam classification endpoint."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    subject = data.get("subject", "").strip()
    mode = data.get("mode", "email")

    if not text:
        return jsonify({"error": "Message text cannot be empty."}), 400

    start_time = time.time()
    result = engine.predict(text=text, subject=subject, mode=mode)
    result["latency_ms"] = round((time.time() - start_time) * 1000, 2)

    return jsonify(result)


@app.route("/api/batch", methods=["POST"])
def api_batch():
    """Batch spam classification for multiple items or CSV files."""
    messages = []
    
    # Check if a file was uploaded
    if "file" in request.files:
        uploaded_file = request.files["file"]
        filename = uploaded_file.filename.lower()
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        
        if filename.endswith(".csv"):
            reader = csv.reader(io.StringIO(content))
            header = next(reader, None)
            text_col_idx = 0
            # Detect text column if named 'text', 'message', 'body', 'content'
            if header:
                for idx, col in enumerate(header):
                    if col.strip().lower() in ["text", "message", "body", "email", "sms", "content"]:
                        text_col_idx = idx
                        break
                # If header didn't look like text, rewind or use row
                for row in reader:
                    if row and len(row) > text_col_idx and row[text_col_idx].strip():
                        messages.append(row[text_col_idx].strip())
        else:
            # Treat as text file, 1 message per non-empty line
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            messages.extend(lines)
    else:
        # Check JSON payload
        data = request.get_json(force=True, silent=True) or {}
        messages = data.get("items", [])

    if not messages:
        return jsonify({"error": "No messages provided for batch analysis."}), 400

    # Limit to maximum 500 items per batch for UI performance
    messages = messages[:500]

    start_time = time.time()
    results = []
    spam_count = 0
    suspicious_count = 0
    ham_count = 0
    total_score = 0.0

    for idx, msg in enumerate(messages):
        pred = engine.predict(msg, mode="email")
        score = pred.get("spam_score", 0.0)
        total_score += score
        cls = pred.get("classification", "HAM")

        if cls == "SPAM":
            spam_count += 1
        elif cls == "SUSPICIOUS":
            suspicious_count += 1
        else:
            ham_count += 1

        top_trigger = pred["trigger_words"][0]["word"] if pred.get("trigger_words") else "-"

        results.append({
            "id": idx + 1,
            "text": msg[:150] + ("..." if len(msg) > 150 else ""),
            "full_text": msg,
            "classification": cls,
            "risk_level": pred.get("risk_level", "SAFE"),
            "spam_score": score,
            "top_trigger": top_trigger,
            "badge_color": pred.get("badge_color", "success")
        })

    duration_ms = round((time.time() - start_time) * 1000, 2)
    total = len(results)

    summary = {
        "total": total,
        "spam_count": spam_count,
        "suspicious_count": suspicious_count,
        "ham_count": ham_count,
        "spam_rate": round((spam_count / total) * 100, 1) if total > 0 else 0,
        "avg_risk_score": round(total_score / total, 1) if total > 0 else 0,
        "processing_time_ms": duration_ms
    }

    return jsonify({
        "summary": summary,
        "items": results
    })


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Retrieve model training metrics and vocabulary statistics."""
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return jsonify(metadata)
        except Exception as e:
            return jsonify({"error": f"Failed to read metadata: {e}"}), 500
    return jsonify({"error": "Model metadata not found. Train model first."}), 404


@app.route("/api/examples", methods=["GET"])
def api_examples():
    """Return pre-built curated message examples."""
    return jsonify({"examples": CURATED_EXAMPLES})


@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model_loaded": engine.is_loaded,
        "uptime": time.strftime("%Y-%m-%d %H:%M:%S")
    })


if __name__ == "__main__":
    print("[*] Starting Spamify Web Server at http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
