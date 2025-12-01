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
<meta property="og:image" content="https://raw.githubusercontent.com/Voodoorae/ai-visibility-audit/main/Gemini_Generated_Image_tzlldqtzlldqtzll.jpg">
<meta property="og:url" content="https://ai-visibility-audit.streamlit.app">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://raw.githubusercontent.com/Voodoorae/ai-visibility-audit/main/Gemini_Generated_Image_tzlldqtzlldqtzll.jpg">
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
    
    /* Hide Anchor Links on Headers */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a {
        display: none !important;
    }
    a.anchor-link {
        display: none !important;
    }
    
    /* Headers */
    h1 { 
        color: #FFDA47 !important; 
        font-family: 'Spectral', serif !important; 
        font-weight: 800; 
        text-align: center; 
        margin-top: 0px;
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

    /* Buttons */
    button {
        background-color: #FFDA47 !important; 
        color: #000000 !important;
        font-weight: 900 !important; 
        border-radius: 8px !important; 
        border: none !important; 
        height: 50px !important; 
        width: 100% !important; 
        font-size: 16px !important; 
        text-transform: uppercase !important; 
        letter-spacing: 1px !important; 
        transition: transform 0.1s ease-in-out !important; 
        font-family: 'Inter', sans-serif !important; 
    }

    button:hover {
        background-color: white !important; 
        color: #000000 !important; 
        transform: scale(1.02); 
        border: none !important;
    }
    
    /* HTML Link Buttons */
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
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    }
    .score-circle { 
        font-size: 36px !important; 
        font-weight: 800; 
        line-height: 1; 
        margin-bottom: 5px; 
        color: #FFDA47;
        font-family: 'Spectral', serif; 
    }
    .score-label { 
        font-size: 12px; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        color: #8899A6; 
        font-family: 'Inter', sans-serif; 
    }
    .verdict-text { 
        font-size: 20px; 
        font-weight: 800; 
        margin-top: 5px; 
        font-family: 'Spectral', serif; 
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
    
    .tripwire-box { 
        background: linear-gradient(135deg, #0B3C5D 0%, #1A1F2A 100%); 
        border: 2px solid #FFDA47; 
        border-radius: 12px; 
        padding: 20px; 
        margin-top: 10px; 
        margin-bottom: 20px;
        text-align: center; 
    }
    
    .signals-header {
        text-align: center;
        color: #FFDA47;
        font-family: 'Spectral', serif;
        font-weight: 700;
        font-size: 22px;
        margin-top: 30px;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
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
    
    /* Admin Panel Styles */
    .admin-box {
        border: 1px solid #444;
        padding: 15px;
        border-radius: 5px;
        background-color: #222;
        margin-top: 50px;
    }
    
    /* Form Input Fix */
    .stTextInput > div > div > input {
        background-color: #2D3342;
        color: white;
        border: 1px solid #4A5568;
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
    # 1. Save to Local CSV (Backup)
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

    # 2. Send to GoHighLevel (Automation)
    # UPDATED: Added Visual Debugging
    if "PASTE_YOUR_GHL" not in GHL_WEBHOOK_URL:
        try:
            payload = {
                "name": name,
                "email": email,
                "website": url,
                "customData": {
                    "audit_score": score,
                    "audit_verdict": verdict
                },
                "tags": ["Source: AI Audit App"]
            }
            # Increased timeout to 5s
            response = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
            
            # Check response status
            if response.status_code == 200 or response.status_code == 201:
                st.toast("System: Data sent to GHL successfully", icon="✅")
                print(f"GHL Success: {response.status_code}")
            else:
                st.error(f"GHL Error: Received Status Code {response.status_code}")
                st.write(f"GHL Message: {response.text}")
                print(f"GHL Failed with {response.status_code}")
                
        except Exception as e:
            st.error(f"Connection Error to GHL: {e}")
            print(f"GHL Webhook Failed: {e}")
    else:
        print("GHL Webhook not configured yet.")

def update_leads(df):
    df.to_csv(LEADS_
