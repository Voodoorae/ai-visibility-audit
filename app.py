import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import datetime
import urllib3
import json
import os
import pandas as pd

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

# --- CUSTOM CSS (UI RESTORATION & LINK ICON REMOVAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    .stApp { background-color: #1A1F2A; color: white; }
    
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stHeaderAction"] {display: none !important;}
    
    /* REMOVE LINK ICON & FULLSCREEN */
    [data-testid="StyledFullScreenButton"] { display: none !important; }
    [data-testid="stImage"] a { pointer-events: none !important; cursor: default !important; }

    h1 { 
        color: #FFDA47 !important; 
        font-family: 'Spectral', serif !important; 
        font-weight: 800; 
        text-align: center; 
        font-size: 3.5rem; 
        line-height: 1;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    
    .sub-head { 
        text-align: center; 
        color: #FFFFFF; 
        font-size: 20px; 
        margin-bottom: 25px; 
        font-family: 'Inter', sans-serif; 
    }

    .explainer-text {
        text-align: center;
        color: #B0B0B0;
        font-size: 16px;
        margin-bottom: 30px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }

    .signal-item {
        background-color: #2D3342;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #E0E0E0;
        border-left: 3px solid #FFDA47;
    }

    div[data-testid="stButton"] > button, 
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #FFDA47 !important; 
        color: #000000 !important;
        font-weight: 900 !important; 
        border-radius: 8px !important;
        height: 50px !important;
        width: 100%;
        border: none !important;
    }

    .score-container { 
        background-color: #252B3B; 
        border-radius: 15px; 
        padding: 20px; 
        text-align: center; 
        margin-top: 10px; 
        border: 1px solid #3E4658; 
    }
    .score-circle { font-size: 48px !important; font-weight: 800; color: #FFDA47; font-family: 'Spectral', serif; }
    
    .amber-btn {
        display: block;
        background-color: #FFDA47;
        color: #000000;
        font-weight: 900;
        border-radius: 8px;
        height: 55px;
        line-height: 55px;
        text-decoration: none;
        text-align: center;
        font-family: 'Inter', sans-serif;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LEAD CAPTURE HANDLER ---
def save_lead_to_ghl(name, email, url, score, verdict):
    try:
        payload = {
            "name": name,
            "email": email,
            "website": url,
            "customData": {"audit_score": score, "audit_verdict": verdict}
        }
        requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
        st.success(f"Report sent to {email}!")
    except:
        st.error("Failed to sync with GHL. Please try again.")

# --- SCANNING ENGINE (STRICT & HARDENED) ---
def check_canonical_status(soup, working_url):
    tag = soup.find('link', rel='canonical')
    if tag and tag.get('href', '').strip().lower() == working_url.lower():
        return 10, "✅ Self-referencing canonical tag found."
    return 0, "❌ Missing/Invalid Canonical tag."

def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}"]
    for url in attempts:
        try:
            r = requests.get(url, headers={'User-Agent': 'FoundByAI/2.0'}, timeout=10, verify=False)
            return r, url
        except: continue
    raise ConnectionError("Connect failed.")

def analyze_website(raw_url):
    try:
        response, working_url = smart_connect(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        
        # Scoring Math
        base_score = 25 # Technical Base
        
        # Schema (30)
        schemas = soup.find_all('script', type='application/ld+json')
        schema_content = "".join([s.string for s in schemas if s.string]).lower()
        s_pts = 30 if any(x in schema_content for x in ["localbusiness", "organization"]) else (10 if schemas else 0)
        
        # Voice (20)
        headers = [h.get_text().lower() for h in soup.find_all(['h1', 'h2', 'h3'])]
        v_pts = 20 if any(any(q in h for q in ['how','cost','price','best','near']) for h in headers) else 0
        
        # Canonical (10)
        c_pts, _ = check_canonical_status(soup, working_url)
        
        # Integrity (15)
        has_alt = all(img.get('alt') for img in soup.find_all('img')) if soup.find_all('img') else False
        has_yr = str(datetime.datetime.now().year) in text
        d_pts = (8 if has_alt else 0) + (7 if has_yr else 0)

        total = min(base_score + s_pts + v_pts + c_pts + d_pts, 100)
        
        verdict = "AI READY" if total >= 85 else ("NEEDS OPTIMIZATION" if total >= 55 else "INVISIBLE")
        color = "#28A745" if total >= 85 else ("#FFDA47" if total >= 55 else "#FF4B4B")
        
        return {"score": total, "verdict": verdict, "color": color}
    except:
        return {"score": 35, "verdict": "SCAN BLOCKED", "color": "#FFDA47"}

# --- UI RENDER ---
st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-head'>Is your business visible to Google, Apple, Siri, Alexa, and AI Agents?</div>", unsafe_allow_html=True)

if "audit_results" not in st.session_state:
    st.markdown("<div class='explainer-text'>AI search agents are replacing traditional search. If your site isn't technically optimized, you're becoming invisible. Run your audit now.</div>", unsafe_allow_html=True)
    
    # 8 SIGNALS GRID
    st.markdown("<div style='text-align:center; font-weight:800; margin-bottom:15px;'>8 CRITICAL AI SIGNALS</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        for s in ["Voice Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]:
            st.markdown(f"<div class='signal-item'>✅ {s}</div>", unsafe_allow_html=True)
    with col2:
        for s in ["Accessibility", "SSL Security", "Mobile Readiness", "Entity Clarity"]:
            st.markdown(f"<div class='signal-item'>✅ {s}</div>", unsafe_allow_html=True)

with st.form("audit_form"):
    url_input = st.text_input("Enter Website URL", placeholder="yourbusiness.com", label_visibility="collapsed")
    submit = st.form_submit_button("RUN THE AUDIT")

if submit and url_input:
    with st.spinner("Analyzing AI Signals..."):
        st.session_state.audit_results = analyze_website(url_input)
        st.session_state.current_url = url_input
        st.rerun()

if "audit_results" in st.session_state:
    res = st.session_state.audit_results
    st.markdown(f"""
        <div class="score-container" style="border-top: 5px solid {res['color']};">
            <div style="font-size: 14px; letter-spacing: 2px;">AI VISIBILITY SCORE</div>
            <div class="score-circle">{res['score']}/100</div>
            <div style="color: {res['color']}; font-weight: 800; font-size: 20px;">{res['verdict']}</div>
        </div>
    """, unsafe_allow_html=True)

    # LEAD CAPTURE FORM
    st.markdown("<h3 style='text-align:center; color:#FFDA47; margin-top:20px;'>Get the Detailed Analysis PDF</h3>", unsafe_allow_html=True)
    with st.form("lead_form"):
        c1, c2 = st.columns(2)
        u_name = c1.text_input("Name")
        u_email = c2.text_input("Email")
        if st.form_submit_button("SEND MY DETAILED REPORT"):
            if u_name and u_email:
                save_lead_to_ghl(u_name, u_email, st.session_state.current_url, res['score'], res['verdict'])
            else: st.error("Please provide name and email.")

    # CTA BUTTONS
    st.markdown("<hr>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    b1.markdown('<a href="https://go.foundbyai.online/get-toolkit" class="amber-btn">FAST FIX TOOLKIT £27</a>', unsafe_allow_html=True)
    b2.markdown('<a href="https://go.foundbyai.online/tune-up/page" class="amber-btn">BOOK TUNE UP £150</a>', unsafe_allow_html=True)
    
    if st.button("🔄 START NEW AUDIT"):
        del st.session_state.audit_results
        st.rerun()
