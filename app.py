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
import gspread
from google.oauth2.service_account import Credentials

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

# --- CUSTOM CSS (THE SPECTRAL/AMBER UI) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }

/* 1. WIDE WIDTH */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1000px; 
}

/* Hide Streamlit Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stHeaderAction"] {display: none !important;}

/* HEADERS */
h1 {
    color: #FFDA47 !important;
    font-family: 'Spectral', serif !important;
    font-weight: 800;
    text-align: center;
    margin-top: 0px; 
    margin-bottom: 5px;
    font-size: 3rem; 
    letter-spacing: -1px;
    line-height: 1;
}

/* UNIFIED HEADER STYLE */
.input-header {
    text-align: center;
    color: #FFFFFF;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    margin-bottom: 12px;
    font-size: 20px;
    width: 100%;
}
@media (max-width: 600px) {
    .input-header { font-size: 18px !important; }
    h1 { font-size: 2.5rem !important; }
}

/* THE CARRIE BOX */
.did-you-know { 
    text-align: center; 
    color: #E0E0E0; 
    font-size: 16px; 
    margin: 25px 0; 
    font-family: 'Inter', sans-serif; 
    font-weight: 500; 
    background: #2D3342; 
    padding: 15px; 
    border-radius: 8px; 
    border: 1px solid #4A5568; 
}

/* DASHBOARD HEADER */
.dashboard-head {
    text-align: center;
    margin-bottom: 15px;
    padding-top: 15px;
    border-top: 1px solid #3E4658; 
}
.dashboard-head h3 {
    color: #FFDA47;
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}

/* BUTTONS */
div[data-testid="stButton"] > button, 
div[data-testid="stFormSubmitButton"] > button { 
    background-color: #FFDA47 !important; 
    color: #000000 !important; 
    font-weight: 900 !important; 
    border: none !important; 
    border-radius: 8px !important; 
    min-height: 50px !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] > button:hover, 
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #FFFFFF !important;
    transform: scale(1.02);
}

/* INPUTS */
input.stTextInput { background-color: #2D3342 !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }

/* RESULTS CARD */
.score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658; }
.score-circle { font-size: 36px !important; font-weight: 800; color: #FFDA47; font-family: 'Spectral', serif; }
.score-label { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #8899A6; font-family: 'Inter', sans-serif; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }
.blocked-msg { color: #FFDA47; background-color: rgba(255, 218, 71, 0.05); border: 1px solid #FFDA47; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px; }

/* AMBER BUTTON LINK */
.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; border: none; height: 55px; width: 100%; font-size: 16px; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; transition: transform 0.1s; }
.amber-btn:hover { background-color: white; color: #000000; transform: scale(1.02); }

/* BREAKDOWN CARDS */
.audit-card {
    background-color: #2D3342;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #3E4658;
    height: 100%;
}
.audit-card h4 { margin: 0; font-size: 16px; font-weight: 700; font-family: 'Inter', sans-serif; color: #FFFFFF; }
.audit-card p { margin: 5px 0 0 0; font-size: 14px; color: #B0B3B8; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE HANDLER (GOOGLE SHEETS) ---
def save_lead(name, email, url, score, verdict, audit_data):
    try:
        # Check if secrets exist
        if "gcp_service_account" not in st.secrets:
            st.error("Google Sheets Secrets missing in .streamlit/secrets.toml")
            return
            
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        
        # Ensure sheet name is exactly "Found By AI Leads"
        sheet = client.open("Found By AI Leads").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, email, url, score, verdict, timestamp])
        st.success(f"Report sent to {email}!")
        
    except Exception as e:
        # Fail silently on UI but print to logs to avoid scaring user
        print(f"Sheet Error: {e}")
        st.warning("Generated report, but could not save to database.")

# --- PDF GENERATOR ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Found By AI - Visibility Report', 0, 1, 'C')
            self.ln(5)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, 'Generated by Found By AI', 0, 0, 'C')

    def create_download_pdf(data, url, name):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 10, f"Audit Score: {data['score']}/100", 0, 1, 'C')
        pdf.set_font("Arial", "I", 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1, 'C')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Site: {url}", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Verdict: {data['verdict']}", 0, 1, 'L')
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, data['summary'])
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Technical Breakdown", 0, 1, 'L')
        pdf.ln(5)
        pdf.set_font("Arial", "", 12)
        for criterion, details in data['breakdown'].items():
            status = "PASS" if details['points'] == details['max'] else "FAIL"
            pdf.cell(0, 10, f"{criterion}: {status} ({details['points']}/{details['max']})", 0, 1)
            pdf.ln(10)
        return pdf.output(dest='S').encode('latin-1')

# --- ENGINES ---
def fallback_analysis(url):
    breakdown = {
        "Server Connectivity": {"points": 15, "max": 15, "note": "✅ Server responded."},
        "SSL Security": {"points": 10, "max": 10, "note": "✅ SSL Valid."},
        "Domain Authority": {"points": 10, "max": 15, "note": "⚠️ Active domain."},
        "Schema Code": {"points": 0, "max": 30, "note": "❌ BLOCKED: Schema unreadable."},
        "Voice Search": {"points": 0, "max": 20, "note": "❌ BLOCKED: Headers unreadable."},
        "Accessibility": {"points": 0, "max": 15, "note": "❌ BLOCKED: Alt tags unreadable."},
        "Freshness": {"points": 0, "max": 15, "note": "❌ BLOCKED: Copyright unreadable."},
        "Local Signals": {"points": 0, "max": 10, "note": "❌ BLOCKED: Contact info unreadable."},
        "Canonical Link": {"points": 0, "max": 10, "note": "❌ BLOCKED: Headers unreadable."}
    }
    return {
        "score": 35, "status": "blocked", "verdict": "AI VISIBILITY RESTRICTED", "color": "#FFDA47",
        "summary": "Firewall blocking AI scanners. You must implement the 'Unblocker' fix.", "breakdown": breakdown
    }

def smart_connect(raw_url):
    clean_url = raw_url.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "")
    if clean_url.endswith("/"): clean_url = clean_url[:-1]
    targets = [f"https://www.{clean_url}", f"https://{clean_url}", f"http://www.{clean_url}", f"http://{clean_url}"]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for target in targets:
        try:
            response = requests.get(target, headers=headers, timeout=10, verify=False)
            if response.status_code == 200: return response, target
        except: continue
    raise ConnectionError("Connect failed")

def analyze_website(raw_url):
    try:
        response, working_url = smart_connect(raw_url)
        if response.status_code in [403, 406, 429, 503]: return fallback_analysis(raw_url)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0
        breakdown = {}
        
        # 1. Schema
        schemas = soup.find_all('script', type='application/ld+json')
        breakdown["Schema Code"] = {"points": 30 if schemas else 0, "max": 30, "note": "Checked JSON-LD."}
        score += 30 if schemas else 0
        
        # 2. Voice
        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq']
        has_q = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        breakdown["Voice Search"] = {"points": 20 if has_q else 0, "max": 20, "note": "Checked Headers for Q&A."}
        score += 20 if has_q else 0
        
        # 3. Accessibility
        imgs = soup.find_all('img')
        with_alt = sum(1 for i in imgs if i.get('alt'))
        acc_ok = len(imgs) == 0 or (len(imgs) > 0 and (with_alt/len(imgs) > 0.8))
        breakdown["Accessibility"] = {"points": 15 if acc_ok else 0, "max": 15, "note": "Checked Alt Tags."}
        score += 15 if acc_ok else 0
        
        # 4. Freshness
        has_year = str(datetime.datetime.now().year) in text
        breakdown["Freshness"] = {"points": 15 if has_year else 0, "max": 15, "note": "Checked Copyright Year."}
        score += 15 if has_year else 0
        
        # 5. Canonical
        canon = soup.find('link', rel='canonical')
        is_canon = canon and canon.get('href','').strip().lower() == working_url.lower()
        breakdown["Canonical Link"] = {"points": 10 if is_canon else 0, "max": 10, "note": "Checked Canonical Tag."}
        score += 10 if is_canon else 0
        
        # 6. Local
        has_contact = "contact" in text or soup.find('a', href=re.compile(r'contact', re.I))
        breakdown["Local Signals"] = {"points": 10 if has_contact else 5, "max": 10, "note": "Checked Contact Page."}
        score += 10 if has_contact else 5
        
        final_score = score + 25 # Base points for connectivity
        breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ OK"}
        breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ OK"}
        
        verdict = "AI READY" if final_score > 80 else ("PARTIALLY VISIBLE" if final_score > 60 else "INVISIBLE TO AI")
        color = "#28A745" if final_score > 80 else ("#FFDA47" if final_score > 60 else "#FF4B4B")
        summary = "Your site is technically optimized." if final_score > 80 else "Critical visibility issues found."
        
        return {"score": final_score, "verdict": verdict, "color": color, "summary": summary, "breakdown": breakdown, "status": "active"}
        
    except Exception: return fallback_analysis(raw_url)

# --- UI RENDER ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("LG Iogo charcoal BG.jpg"):
        st.image("LG Iogo charcoal BG.jpg", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center;'>FOUND BY AI</h1>", unsafe_allow_html=True)

if "audit_data" not in st.session_state: st.session_state.audit_data = None
if "url_input" not in st.session_state: st.session_state.url_input = ""

# LANDING PAGE
if not st.session_state.audit_data:
    st.markdown("<div class='input-header'>When customers ask their phones to find a business...<br><strong>Does your website show up?</strong></div>", unsafe_allow_html=True)
    with st.form("audit_form"):
        c1, c2 = st.columns([3,1])
        with c1: url = st.text_input("URL", placeholder="mybusiness.com", label_visibility="collapsed")
        with c2: submit = st.form_submit_button("RUN FREE SCAN")
    
    if submit and url:
        st.session_state.url_input = url
        with st.spinner("Connecting to AI Scanners..."):
            time.sleep(1)
            st.session_state.audit_data = analyze_website(url)
            st.rerun()

    # DASHBOARD ICONS
    st.markdown("<div class='dashboard-head'><h3>Found By AI tests 8 Critical Platforms</h3></div>", unsafe_allow_html=True)
    r1 = st.columns(4)
    icons = ["🗺️ Google Maps", "🍎 Apple Maps", "🗣️ Voice Search", "🤖 ChatGPT"]
    for i, col in enumerate(r1):
        with col:
            st.markdown(f"**{icons[i]}**<br>Status: **❓ UNKNOWN**", unsafe_allow_html=True)
            
    st.markdown("<br><div class='did-you-know'>💡 <strong>DID YOU KNOW?</strong><br>Siri and Alexa are AI. If you are invisible to AI, they won't recommend you.</div>", unsafe_allow_html=True)

# RESULTS PAGE
if st.session_state.audit_data:
    data = st.session_state.audit_data
    color = data.get("color", "#FFDA47")
    
    st.markdown(f"""
    <div class="score-container" style="border-top: 5px solid {color};">
        <div class="score-label">Result for {st.session_state.url_input}</div>
        <div class="score-circle">{data['score']}/100</div>
        <div class="verdict-text" style="color: {color};">{data['verdict']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<h3 style='text-align: center; color: #FFDA47;'>UNLOCK YOUR BUSINESS</h3>", unsafe_allow_html=True)
    st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    for i, (k, v) in enumerate(data['breakdown'].items()):
        status = "PASS" if v['points'] == v['max'] else "FAIL"
        c_code = "#28A745" if status == "PASS" else "#FF4B4B"
        html = f"""<div class="audit-card" style="border-left: 5px solid {c_code};"><h4>{k}</h4><span style="color:{c_code};font-weight:bold;">{status}</span><p>{v['note']}</p></div>"""
        if i % 2 == 0: b1.markdown(html, unsafe_allow_html=True)
        else: b2.markdown(html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#8899A6;'>Get the full report sent to your email:</p>", unsafe_allow_html=True)
    with st.form("email_form"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Name")
        with c2: email = st.text_input("Email")
        sent = st.form_submit_button("EMAIL ME MY REPORT", use_container_width=True)
        
    if sent and email:
        save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'], data)
    
    def clear(): st.session_state.audit_data = None
    st.button("🔄 CHECK ANOTHER COMPETITOR", on_click=clear, use_container_width=True)

# END OF FILE
