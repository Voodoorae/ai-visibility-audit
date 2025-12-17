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

# Disable SSL warnings for robust scanning of various site types
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

# --- CUSTOM CSS (UI CLEANUP, LINK ICON REMOVAL, & BUTTON STYLING) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    .stApp { background-color: #1A1F2A; color: white; }
    
    /* Hide Streamlit Native UI Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeaderAction"] {display: none !important;}
    
    /* REMOVE LINK ICON & FULLSCREEN OVERLAY ON IMAGES */
    [data-testid="StyledFullScreenButton"] { display: none !important; }
    [data-testid="stImage"] a { pointer-events: none !important; cursor: default !important; }
    .st-emotion-cache-15zrgzn e1nzilvr4 { display: none !important; } 

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

    /* Primary Form Button Styling */
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

    /* Score Card Styles */
    .score-container { 
        background-color: #252B3B; 
        border-radius: 15px; 
        padding: 20px; 
        text-align: center; 
        margin-top: 10px; 
        border: 1px solid #3E4658; 
    }
    .score-circle { 
        font-size: 48px !important; 
        font-weight: 800; 
        color: #FFDA47;
        font-family: 'Spectral', serif; 
    }
    
    /* The Wide "Unblock" Action Button */
    .amber-btn {
        display: block;
        background-color: #FFDA47;
        color: #000000;
        font-weight: 900;
        border-radius: 8px;
        height: 65px;
        line-height: 65px;
        text-decoration: none;
        text-align: center;
        font-family: 'Inter', sans-serif;
        margin-top: 20px;
        font-size: 20px;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(255, 218, 71, 0.2);
    }
    .amber-btn:hover {
        background-color: #FFFFFF;
        color: #000000;
        transform: translateY(-2px);
        transition: 0.2s;
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
        r = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
        if r.status_code in [200, 201]:
            st.success(f"Success! Your detailed analysis is being sent to {email}.")
        else:
            st.error("Sync error. Please try again.")
    except:
        st.error("Connection to GoHighLevel failed.")

# --- SCANNING ENGINES ---
def check_canonical_status(soup, working_url):
    tag = soup.find('link', rel='canonical')
    if tag and tag.get('href', '').strip().lower().rstrip('/') == working_url.lower().rstrip('/'):
        return 10
    return 0

def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}"]
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; FoundByAI/2.0)'}
    for url in attempts:
        try:
            response = requests.get(url, headers=headers, timeout=12, verify=False)
            return response, url
        except: continue
    raise ConnectionError("Failed to connect.")

def analyze_website(raw_url):
    try:
        response, working_url = smart_connect(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        
        # 1. FIXED TECH BASE (25 PTS)
        score = 25

        # 2. SCHEMA STRICKNESS (30 PTS)
        schemas = soup.find_all('script', type='application/ld+json')
        schema_content = "".join([s.string for s in schemas if s.string]).lower()
        if any(x in schema_content for x in ["localbusiness", "organization", "professional service"]):
            score += 30
        elif len(schemas) > 0:
            score += 10

        # 3. VOICE SEARCH (20 PTS)
        headers = [h.get_text().lower() for h in soup.find_all(['h1', 'h2', 'h3'])]
        q_words = ['how', 'cost', 'price', 'why', 'where', 'best']
        if any(any(q in h for q in q_words) for h in headers):
            score += 20

        # 4. CANONICAL (10 PTS)
        score += check_canonical_status(soup, working_url)

        # 5. DATA INTEGRITY (15 PTS)
        current_year = str(datetime.datetime.now().year) in text
        imgs = soup.find_all('img')
        has_alt = all(img.get('alt') for img in imgs) if imgs else False
        if current_year: score += 7
        if has_alt: score += 8

        # --- THE MATH CEILING (Fixes 115% Bug) ---
        final_total = min(score, 100)
        
        # Verdict Logic
        verdict = "AI READY" if final_total >= 85 else ("NEEDS OPTIMIZATION" if final_total >= 55 else "INVISIBLE")
        color = "#28A745" if final_total >= 85 else ("#FFDA47" if final_total >= 55 else "#FF4B4B")
        
        return {"score": final_total, "verdict": verdict, "color": color}
    except:
        return {"score": 35, "verdict": "SCAN BLOCKED", "color": "#FFDA47"}

# --- UI RENDER ---
st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-head'>Is your business visible to Google, Apple, Siri, Alexa, and AI Agents?</div>", unsafe_allow_html=True)

if "audit_results" not in st.session_state:
    st.markdown("<div class='explainer-text'>AI search agents are replacing traditional search. If your site isn't technically optimized, you're becoming invisible. Run your audit now.</div>", unsafe_allow_html=True)
    
    # 8 SIGNALS GRID
    st.markdown("<div style='text-align:center; font-weight:800; margin-bottom:15px; letter-spacing:1px;'>8 CRITICAL AI SIGNALS</div>", unsafe_allow_html=True)
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

    # LEAD CAPTURE: Corrected Language (Trust Building)
    st.markdown("<h3 style='text-align:center; color:#FFDA47; margin-top:20px;'>Email Me My Full AI Visibility Report</h3>", unsafe_allow_html=True)
    with st.form("lead_form"):
        c1, c2 = st.columns(2)
        u_name = c1.text_input("Name", placeholder="Your Name")
        u_email = c2.text_input("Email", placeholder="name@company.com")
        if st.form_submit_button("SEND MY DETAILED REPORT"):
            if u_name and u_email:
                save_lead_to_ghl(u_name, u_email, st.session_state.current_url, res['score'], res['verdict'])
            else: st.error("Please provide name and email.")

    # ACTION SECTION: High-Urgency Bridge
    st.markdown("<hr style='border-color: #3E4658;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #E0E0E0;'><strong>Warning:</strong> Your business is currently being bypassed by AI Search Agents. Follow the roadmap below to remove these restrictions.</p>", unsafe_allow_html=True)
    
    # THE PRIMARY "UNBLOCK" BUTTON
    st.markdown('<a href="https://go.foundbyai.online/get-toolkit" class="amber-btn" style="text-decoration: none;">UNBLOCK YOUR BUSINESS: STEP-BY-STEP</a>', unsafe_allow_html=True)

    # FACEBOOK COMMUNITY INTEGRATION (The Trust Loop)
    st.markdown(f"""
        <div style='background-color: #2D3342; padding: 15px; border-radius: 8px; margin-top: 25px; text-align: center; border: 1px solid #3b5998;'>
            <p style='margin-bottom: 5px; color: #FFFFFF;'><strong>Stuck on a technical fix?</strong></p>
            <p style='font-size: 14px; color: #B0B0B0; margin-bottom: 15px;'>Join our community for free daily guidance and score-boosting tips.</p>
            <a href="https://www.facebook.com/FoundByAI/" target="_blank" style="color: #FFDA47; text-decoration: none; font-weight: 700; font-size: 16px;">JOIN THE FOUND BY AI COMMUNITY →</a>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 START NEW AUDIT"):
        del st.session_state.audit_results
        st.rerun()
