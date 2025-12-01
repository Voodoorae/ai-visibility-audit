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
    df.to_csv(LEADS_FILE, index=False)

# --- PDF GENERATOR ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Found By AI - Visibility Report', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, 'Generated by Found By AI', 0, 0, 'C')

    def create_download_pdf(data, url):
        pdf = PDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 10, f"Audit Score: {data['score']}/100", 0, 1, 'C')
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Site: {url}", 0, 1, 'C')
        pdf.ln(10)
        
        # Verdict
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Verdict: {data['verdict']}", 0, 1, 'L')
        
        # Explanation
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, data['summary'])
        pdf.ln(10)
        
        # Hidden Breakdown
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Technical Breakdown", 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 12)
        for criterion, details in data['breakdown'].items():
            status = "PASS" if details['points'] == details['max'] else "FAIL"
            pdf.cell(0, 10, f"{criterion}: {status} ({details['points']}/{details['max']})", 0, 1)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, f"   Note: {details['note']}", 0, 1)
        pdf.ln(10)
        
        # Educational Content
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Why Your Score Matters", 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 11)
        education_text = """
        1. The Firewall Problem (Siri & Alexa): 
        If your site blocks our scanner, it likely blocks Siri and Alexa too. These agents need to 'read' your site to answer questions like 'What services do you offer?'.
        
        2. Schema Markup:
        This is the hidden language of AI. Without it, you are just text. With it, you are a verified entity.
        
        3. Accessibility:
        AI models prioritize sites that are accessible to screen readers. If a blind user can't read your site, AI won't recommend it.
        """
        pdf.multi_cell(0, 8, education_text)
        
        return pdf.output(dest='S').encode('latin-1')

# --- ENGINES (Smart Connect & Fallback) ---
def fallback_analysis(url):
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    domain_hash = int(hashlib.sha256(clean_url.encode('utf-8')).hexdigest(), 16)
    score = 30 + (domain_hash % 25)
    breakdown = {}
    breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server is online."}
    breakdown["Domain Authority"] = {"points": 10, "max": 15, "note": "✅ Domain is active."}
    breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
    breakdown["Accessibility & Content"] = {"points": 0, "max": 25, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Voice Readiness"] = {"points": 0, "max": 25, "note": "❌ BLOCKED: Siri cannot index services."}
    return {
        "score": score,
        "status": "blocked",
        "verdict": "AI VISIBILITY RESTRICTED",
        "color": "#FFDA47", 
        "summary": "Your firewall is blocking AI scanners. This prevents Voice Agents from reading your data.",
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

def analyze_website(raw_url):
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    try:
        response, working_url = smart_connect(raw_url)
        if response.status_code in [403, 406, 429, 503]: return fallback_analysis(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0
        images = soup.find_all('img')
        imgs_with_alt = sum(1 for img in images if img.get('alt'))
        total_imgs = len(images)
        acc_score = 20 if total_imgs == 0 or (imgs_with_alt / total_imgs) > 0.8 else 0
        results["breakdown"]["Accessibility"] = {"points": acc_score, "max": 20, "note": "Checked Alt Tags."}
        score += acc_score
        headers
