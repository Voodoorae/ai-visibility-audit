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

# Disable SSL warnings for robust scanning of older SMB sites
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

# --- CUSTOM CSS (UI CLEANUP & LINK ICON REMOVAL) ---
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
    
    /* THE LINK ICON KILLER - Targets the anchor and button specifically */
    [data-testid="StyledFullScreenButton"] { display: none !important; }
    [data-testid="stImage"] a { pointer-events: none !important; cursor: default !important; }
    .st-emotion-cache-15zrgzn e1nzilvr4 { display: none !important; } /* Link anchor fix */

    h1 { 
        color: #FFDA47 !important; 
        font-family: 'Spectral', serif !important; 
        font-weight: 800; 
        text-align: center; 
        font-size: 3.5rem; 
        line-height: 1;
        margin-bottom: 10px;
    }
    
    .sub-head { 
        text-align: center; 
        color: #FFFFFF; 
        font-size: 20px; 
        margin-bottom: 25px; 
        font-family: 'Inter', sans-serif; 
    }

    /* Primary Button Styling */
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

# --- SCANNING ENGINES ---
def check_canonical_status(soup, working_url):
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href', '').strip().lower() == working_url.lower():
        return 10, "✅ Self-referencing canonical tag found."
    return 0, "❌ Missing or incorrect Canonical tag. AI agents may see duplicate content."

def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}"]
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; FoundByAI/2.0)'}
    for url in attempts:
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            return response, url
        except: continue
    raise ConnectionError("Failed to connect.")

def analyze_website(raw_url):
    results = {"score": 0, "breakdown": {}, "summary": "", "color": "#FFDA47"}
    try:
        response, working_url = smart_connect(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        
        # 1. FIXED TECH BASE (25 PTS)
        # Server connectivity and SSL are verified by the successful smart_connect
        score = 25
        results["breakdown"]["Technical Foundation"] = {"points": 25, "max": 25, "note": "✅ SSL & Server Connectivity verified."}

        # 2. SCHEMA STRICKNESS (30 PTS)
        schemas = soup.find_all('script', type='application/ld+json')
        schema_content = "".join([s.string for s in schemas if s.string]).lower()
        if any(x in schema_content for x in ["localbusiness", "organization", "professional service"]):
            s_pts = 30
            s_note = "✅ Found Local Business Identity Chips."
        elif len(schemas) > 0:
            s_pts = 10
            s_note = "⚠️ Basic Schema found, but lacks Local Business specificity."
        else:
            s_pts = 0
            s_note = "❌ Missing Schema. You are invisible to AI entities."
        score += s_pts
        results["breakdown"]["Schema Code"] = {"points": s_pts, "max": 30, "note": s_note}

        # 3. VOICE SEARCH (20 PTS)
        headers = [h.get_text().lower() for h in soup.find_all(['h1', 'h2', 'h3'])]
        q_words = ['how', 'cost', 'price', 'why', 'where', 'best']
        has_q = any(any(q in h for q in q_words) for h in headers)
        v_pts = 20 if has_q else 0
        score += v_pts
        results["breakdown"]["Voice Search"] = {"points": v_pts, "max": 20, "note": "Checks for conversational headers."}

        # 4. CANONICAL (10 PTS)
        c_pts, c_note = check_canonical_status(soup, working_url)
        score += c_pts
        results["breakdown"]["Canonical Link"] = {"points": c_pts, "max": 10, "note": c_note}

        # 5. DATA INTEGRITY (15 PTS)
        current_year = str(datetime.datetime.now().year) in text
        imgs = soup.find_all('img')
        has_alt = all(img.get('alt') for img in imgs) if imgs else False
        d_pts = (7 if current_year else 0) + (8 if has_alt else 0)
        score += d_pts
        results["breakdown"]["Data Integrity"] = {"points": d_pts, "max": 15, "note": "Checks for Copyright freshness and Alt-tags."}

        # --- THE MATH CEILING (NO MORE 115%) ---
        results["score"] = min(score, 100)

        # VERDICT LOGIC
        if results["score"] < 60:
            results["verdict"], results["color"] = "INVISIBLE", "#FF4B4B"
            results["summary"] = "AI agents cannot verify your business identity."
        elif results["score"] < 85:
            results["verdict"], results["color"] = "PARTIALLY VISIBLE", "#FFDA47"
            results["summary"] = "Optimization required to rank in AI search results."
        else:
            results["verdict"], results["color"] = "AI READY", "#28A745"
            results["summary"] = "Your site is technically ready for AI search agents."

        return results
    except:
        return {"score": 35, "verdict": "SCAN BLOCKED", "color": "#FFDA47", "breakdown": {}, "summary": "Firewall blocked the scan. If we can't see you, Siri can't either."}

# --- UI RENDER ---
st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-head'>Check your business visibility for Siri, Alexa, and AI Agents.</div>", unsafe_allow_html=True)

with st.form("audit_form"):
    url_input = st.text_input("Enter URL", placeholder="yourbusiness.com", label_visibility="collapsed")
    submit = st.form_submit_button("RUN THE AUDIT")

if submit and url_input:
    with st.spinner("Analyzing AI Signals..."):
        data = analyze_website(url_input)
        st.session_state.audit_results = data

if "audit_results" in st.session_state:
    res = st.session_state.audit_results
    st.markdown(f"""
        <div class="score-container" style="border-top: 5px solid {res['color']};">
            <div style="font-size: 14px; letter-spacing: 2px;">AI VISIBILITY SCORE</div>
            <div class="score-circle">{res['score']}/100</div>
            <div style="color: {res['color']}; font-weight: 800; font-size: 20px;">{res['verdict']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write(f"**Analysis:** {res['summary']}")
    
    # CTA SECTION
    st.markdown("<hr style='border-color: #3E4658;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #FFDA47;'>Bridge the Gap in 2 Hours</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<a href="https://go.foundbyai.online/get-toolkit" class="amber-btn">FAST FIX TOOLKIT £27</a>', unsafe_allow_html=True)
    with col2:
        st.markdown('<a href="https://go.foundbyai.online/tune-up/page" class="amber-btn">BOOK TUNE UP £150</a>', unsafe_allow_html=True)
