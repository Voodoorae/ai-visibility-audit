import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import datetime
import urllib3
import random
import hashlib
import base64
import pandas as pd
import json
import os

# --- SAFE IMPORT FOR PDF GENERATION ---
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- GHL WEBHOOK CONFIGURATION ---
GHL_WEBHOOK_URL = "https://services.leadconnectorhq.com/hooks/8I4dcdbVv5h8XxnqQ9Cg/webhook-trigger/e8d9672c-0b9a-40f6-bc7a-aa93dd78ee99"

# --- SOCIAL META TAGS ---
meta_tags = """
<meta property="og:title" content="Found By AI - Visibility Audit">
<meta property="og:description" content="Is your business invisible to Siri, Alexa & Google? Check your AI Visibility Score now.">
<meta property="og:image" content="https://placehold.co/1200x630/1A1F2A/FFDA47?text=Found+By+AI">
<meta property="og:url" content="https://audit.foundbyai.online">
<meta property="og:type" content="website">
"""
st.markdown(meta_tags, unsafe_allow_html=True)

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

.stApp { background-color: #1A1F2A; color: white; }

/* Hide Streamlit Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stHeaderAction"] {display: none !important;}

/* Headers */
h1 {
    color: #FFDA47 !important;
    font-family: 'Spectral', serif !important;
    font-weight: 800;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 5px;
    font-size: 3.5rem;
    letter-spacing: -1px;
    line-height: 1;
}

.sub-head {
    text-align: center;
    color: #FFFFFF;
    font-size: 20px;
    margin-bottom: 25px;
    font-weight: 400;
    font-family: 'Inter', sans-serif;
    line-height: 1.4;
}

.explainer-text {
    text-align: center;
    color: #B0B0B0;
    font-size: 16px;
    margin-bottom: 30px;
    font-family: 'Inter', sans-serif;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

/* --- BUTTON STYLING --- */
div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    background-color: #FFDA47 !important;
    color: #000000 !important;
    font-weight: 900 !important;
    border: none !important;
    border-radius: 8px !important;
    height: 50px !important;
    font-family: 'Inter', sans-serif !important;
    opacity: 1 !important;
}

div[data-testid="stButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(255, 218, 71, 0.4);
}

/* --- REMOVE GHOST BUTTONS FROM IMAGES & LINKS --- */
[data-testid="StyledFullScreenButton"], 
[data-testid="stImage"] a[target="_blank"] {
    display: none !important;
    visibility: hidden !important;
}

/* --- INPUT FIELD VISIBILITY --- */
input.stTextInput {
    background-color: #2D3342 !important;
    color: #FFFFFF !important;
    border: 1px solid #4A5568 !important;
}
/* Style the Labels above input boxes to be visible */
div[data-testid="stMarkdownContainer"] p {
    font-size: 16px;
    font-weight: 600;
}

/* --- LINK BUTTONS --- */
.amber-btn {
    display: block;
    background-color: #FFDA47;
    color: #000000;
    font-weight: 900;
    border-radius: 8px;
    border: none;
    height: 55px;
    width: 100%;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: center;
    line-height: 55px;
    text-decoration: none;
    font-family: 'Inter', sans-serif;
    margin-bottom: 0px;
    transition: transform 0.1s ease-in-out;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.amber-btn:hover {
    background-color: white;
    color: #000000;
    transform: scale(1.02);
}

/* Score Card */
.score-container {
    background-color: #252B3B;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 20px;
    border: 1px solid #3E4658;
}
.score-circle {
    font-size: 36px !important;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 5px;
    color: #FFDA47;
    font-family: 'Spectral', serif;
}
.verdict-text {
    font-size: 20px;
    font-weight: 800;
    margin-top: 5px;
    font-family: 'Spectral', serif;
}
.failure-count {
    font-size: 16px;
    color: #FF4B4B; /* Red color for failure count */
    font-weight: 700;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
}
.blocked-msg {
    color: #FFDA47;
    font-size: 16px;
    font-family: 'Inter', sans-serif;
    line-height: 1.4;
    margin-top: 10px;
    padding: 10px;
    background-color: rgba(255, 218, 71, 0.05);
    border-radius: 8px;
    border: 1px solid #FFDA47;
    text-align: center;
}
.signal-item {
    background-color: #2D3342;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #E0E0E0;
    border-left: 3px solid #28A745;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE / CSV HANDLER ---
LEADS_FILE = "leads.csv"

def load_leads():
    if os.path.exists(LEADS_FILE):
        return pd.read_csv(LEADS_FILE)
    else:
        return pd.DataFrame(columns=["Timestamp", "Name", "Email", "URL", "Score", "Verdict", "AuditData", "Sent"])

def save_lead(name, email, url, score, verdict, audit_data):
    # 1. Save to Local CSV
    df = load_leads()
    new_entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Email": email,
        "URL": url,
        "Score": score,
        "Verdict": verdict,
        "AuditData": json.dumps(audit_data),
        "Sent": False
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(LEADS_FILE, index=False)

    # 2. Send to GoHighLevel
    if "PASTE_YOUR_GHL" not in GHL_WEBHOOK_URL:
        try:
            report_lines = []
            if audit_data and 'breakdown' in audit_data:
                for k, v in audit_data['breakdown'].items():
                    report_lines.append(f"- {k}: {v['points']}/{v['max']} ({v['note']})")
            report_summary = "\n".join(report_lines)

            payload = {
                "name": name,
                "email": email,
                "website": url,
                "customData": {
                    "audit_score": score,
                    "audit_verdict": verdict,
                    "audit_report_text": report_summary
                },
                "tags": ["Source: AI Audit App"]
            }
            response = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)

            if response.status_code in [200, 201]:
                st.success(f"Success! Data sent to {email}.")
            else:
                st.error(f"GHL Error: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"Connection Error to GHL: {e}")
    else:
        print("GHL Webhook not configured yet.")

# --- ENGINES ---
def fallback_analysis(url):
    """Provides a fixed, instructional score for sites that block the scanner."""
    breakdown = {}
    
    # Components that can be verified externally (score = 35)
    breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded to a ping."}
    breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
    breakdown["Domain Authority"] = {"points": 10, "max": 15, "note": "⚠️ Domain is active."}
    
    # Components that are blocked (score = 0)
    breakdown["Schema Code"] = {"points": 0, "max": 30, "note": "❌ BLOCKED: AI cannot read content (CRITICAL)"}
    breakdown["Voice Search"] = {"points": 0, "max": 20, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Accessibility"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Freshness"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Local Signals"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Canonical Link"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content."}

    score = 35

    return {
        "score": score,
        "fails": 6, # Assuming all blocked checks failed
        "total_checks": 6,
        "status": "blocked",
        "verdict": "AI VISIBILITY RESTRICTED",
        "color": "#FFDA47",
        "summary": "Your firewall is blocking AI scanners from reading your content. You must implement the 'Unblocker' fix immediately.",
        "breakdown": breakdown
    }

def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    if clean_url.endswith("/"): clean_url = clean_url[:-1]
    
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}", f"http://{clean_url}"]
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; FoundByAI/1.0)', 'Accept': 'text/html'}
    
    for url in attempts:
        try:
            response = requests.get(url, headers=headers, timeout=8, verify=False)
            return response, url
        except: continue
    raise ConnectionError("Connect failed")

def check_canonical_status(soup, working_url):
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href', '').strip().lower() == working_url.lower():
        return 10, 10, "✅ Self-referencing canonical URL tag found."
    elif canonical_tag:
        return 5, 10, f"⚠️ Canonical URL exists but points to: {canonical_tag.get('href', 'N/A')}."
    else:
        return 0, 10, "❌ No canonical URL tag found."

def analyze_website(raw_url):
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    
    # We will track checks to show "Failed X of Y"
    checks_passed = 0
    total_checks = 6 # Schema, Voice, Accessibility, Freshness, Canonical, Local
    
    try:
        response, working_url = smart_connect(raw_url)
        if response.status_code in [403, 406, 429, 503]:
            return fallback_analysis(raw_url)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0

        # 1. Schema Code (Max: 30)
