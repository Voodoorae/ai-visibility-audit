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
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stHeaderAction"] {display: none !important;}
h1 { color: #FFDA47 !important; font-family: 'Spectral', serif !important; font-weight: 800; text-align: center; font-size: 3.5rem; line-height: 1; margin-bottom: 5px; }
.sub-head { text-align: center; color: #FFFFFF; font-size: 20px; margin-bottom: 25px; font-family: 'Inter', sans-serif; }
.explainer-text { text-align: center; color: #B0B0B0; font-size: 16px; margin-bottom: 30px; font-family: 'Inter', sans-serif; max-width: 600px; margin-left: auto; margin-right: auto;}
.signals-header { text-align: center; color: #FFDA47; font-size: 18px; font-weight: 600; margin-bottom: 15px; font-family: 'Inter', sans-serif; }
div[data-testid="stButton"] > button { background-color: #FFDA47 !important; color: #000000 !important; font-weight: 900 !important; border-radius: 8px !important; height: 50px !important; }
input.stTextInput { background-color: #2D3342 !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }
.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; height: 55px; width: 100%; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; margin-top: 20px; }
.score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658; }
.score-circle { font-size: 36px !important; font-weight: 800; line-height: 1; margin-bottom: 5px; color: #FFDA47; font-family: 'Spectral', serif; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }
.signal-item { background-color: #2D3342; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: 'Inter', sans-serif; font-size: 14px; color: #E0E0E0; border-left: 3px solid #28A745; }
.blocked-msg { color: #FFDA47; font-size: 16px; font-family: 'Inter', sans-serif; margin-top: 10px; padding: 10px; background-color: rgba(255, 218, 71, 0.05); border-radius: 8px; border: 1px solid #FFDA47; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS HELPER FUNCTION ---
def save_to_google_sheet(name, email, url, score, verdict):
    try:
        if "gcp_service_account" not in st.secrets:
            return False

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # FIXED SHEET NAME
        sheet_name = "Found By AI Leads" 
        try:
            sheet = client.open(sheet_name).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"❌ Error: Sheet '{sheet_name}' not found. Please ensure the bot email ({creds.service_account_email}) is an Editor.")
            return False

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [timestamp, str(name), str(email), str(url), str(score), str(verdict), "Pending"]
        sheet.append_row(row_data)
        return True

    except Exception as e:
        st.error(f"⚠️ Google Sheet Error: {e}")
        return False

# --- ENGINES ---
def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    if clean_url.endswith("/"): clean_url = clean_url[:-1]
    
    # SPEED OPTIMIZATION: Reduced timeout to 2.5s
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}", f"http://{clean_url}"]
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; FoundByAI/1.0)', 'Accept': 'text/html'}
    
    for url in attempts:
        try:
            response = requests.get(url, headers=headers, timeout=2.5, verify=False)
            if response.status_code == 200:
                return response, url
        except: continue
    raise ConnectionError("Connect failed")

def analyze_website(raw_url):
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    checks_passed = 0
    total_checks = 6 
    
    try:
        response, working_url = smart_connect(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0

        # CHECKS
        schemas = soup.find_all('script', type='application/ld+json')
        schema_score = 30 if len(schemas) > 0 else 0
        if schema_score > 0: checks_passed += 1
        score += schema_score
        results["breakdown"]["Schema Code"] = {"points": schema_score, "max": 30, "note": "Checked JSON-LD for Identity Chip."}

        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq', 'what is']
        has_questions = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        voice_score = 20 if has_questions else 0
        if voice_score > 0: checks_passed += 1
        score += voice_score
        results["breakdown"]["Voice Search"] = {"points": voice_score, "max": 20, "note": "Checked Headers for Q&A format."}

        images = soup.find_all('img')
        imgs_with_alt = sum(1 for img in images if img.get('alt'))
        total_imgs = len(images)
        acc_score = 15 if total_imgs == 0 or (total_imgs > 0 and (imgs_with_alt / total_imgs) > 0.8) else 0
        if acc_score > 0: checks_passed += 1
        score += acc_score
        results["breakdown"]["Accessibility"] = {"points": acc_score, "max": 15, "note": "Checked Alt Tags (80% minimum)."}

        current_year = str(datetime.datetime.now().year)
        fresh_score = 15 if current_year in text else 0
        if fresh_score > 0: checks_passed += 1
        score += fresh_score
        results["breakdown"]["Freshness"] = {"points": fresh_score, "max": 15, "note": "Checked for current Copyright year."}

        canonical_tag = soup.find('link', rel='canonical')
        can_score = 10 if canonical_tag else 0
        if can_score > 0: checks_passed += 1
        score += can_score
        results["breakdown"]["Canonical Link"] = {"points": can_score, "max": 10, "note": "Checked for Canonical Tag."}

        phone = re.search(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
        loc_score = 10 if phone else 5
        if loc_score == 10: checks_passed += 1
        score += loc_score
        results["breakdown"]["Local Signals"] = {"points": loc_score, "max": 10, "note": "Checked for phone number."}

        # SCORING LOGIC
        final_score = score
        fails = total_checks - checks_passed
        
        # Apply Penalty
        if fails > 0:
            penalty = fails * 10
            final_score = final_score - penalty

        # UNSCORABLE TRAP (The "Bing Fix")
        if final_score < 15:
            results["verdict"] = "AUDIT RESTRICTED"
            results["color"] = "#7D8B99" # Grey/Neutral
            results["summary"] = "This site appears to be a Search Engine or Enterprise Platform."
            results["score"] = "N/A"
            # Fill breakdown so UI doesn't crash
            results["breakdown"] = {"Analysis": {"points": 0, "max": 0, "note": "⚠️ Site structure incompatible with Local Audit."}}
            return results

        # Normal Verdicts
        if schema_score == 0: final_score = min(final_score, 55)
        if voice_score == 0: final_score = min(final_score, 75)
        final_score = max(10, min(final_score, 100)) # Safety Floor

        if final_score < 60: results["verdict"], results["color"] = "INVISIBLE TO AI", "#FF4B4B"
        elif final_score < 86: results["verdict"], results["color"] = "PARTIALLY VISIBLE", "#FFDA47"
        else: results["verdict"], results["color"] = "AI READY", "#28A745"

        results["score"] = final_score
        results["fails"] = fails
        results["total_checks"] = total_checks
        
        return results

    except Exception:
        # Fallback for timeouts/blocks
        return {
            "score": "N/A", "fails": 0, "total_checks": 0,
            "status": "blocked", "verdict": "SECURITY BLOCK", "color": "#FFDA47",
            "summary": "Firewall blocked content scanner.",
            "breakdown": {}
        }

# --- UI RENDER ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
    st.markdown("<div class='sub-head'>Is your business invisible to Siri&nbsp;&&nbsp;AI?</div>", unsafe_allow_html=True)

if "audit_data" not in st.session_state: st.session_state.audit_data = None

with st.form(key='audit_form'):
    col1, col2 = st.columns([3, 1])
    with col1: url = st.text_input("Enter Website URL", placeholder="Enter your website here...", label_visibility="collapsed")
    with col2: submit = st.form_submit_button(label='CHECK MY SCORE')

# --- 8 SIGNALS SECTION (RESTORED) ---
if not st.session_state.audit_data:
    st.markdown("<div class='explainer-text'>Is your site blocking AI scanners? Are you visible to Google, Apple, and Alexa voice agents?<br><strong>Find out how visible you really are.</strong></div>", unsafe_allow_html=True)
    st.markdown("<div class='signals-header'>8 Critical Signals Required for AI Visibility</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        for sig in ["Voice Assistant Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]:
            st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)
    with col2:
        for sig in ["Accessibility Compliance", "SSL Security", "Mobile Readiness", "Entity Clarity"]:
            st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)

# --- PROCESS SUBMISSION ---
if submit and url:
    if "." not in url:
        st.error("Invalid URL.")
    else:
        with st.spinner("Scanning..."):
            st.session_state.audit_data = analyze_website(url)
            data = st.session_state.audit_data
            save_to_google_sheet("Anonymous Scan", "N/A", url, data['score'], data['verdict'])
            st.rerun()

# --- SHOW RESULTS (FIXED BREAKDOWN) ---
if st.session_state.audit_data:
    data = st.session_state.audit_data
    
    # 1. SCORE CARD
    st.markdown(f"""
    <div class="score-container" style="border-top: 5px solid {data.get('color', '#FFDA47')};">
    <div class="score-label">AI VISIBILITY SCORE</div>
    <div class="score-circle">{data['score']}{'/100' if isinstance(data['score'], int) else ''}</div>
    <div class="verdict-text" style="color: {data.get('color', '#FFDA47')};">{data['verdict']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. CRITICAL ALERT BOX
    if isinstance(data['score'], int) and data['score'] < 60:
         st.markdown(f"""
        <div style="background-color: #3b1e1e; border: 1px solid #FF4B4B; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 20px;">
        <span style="font-size: 24px;">⛔</span><br>
        <strong style="color: #FF6B6B; font-size: 18px;">CRITICAL ALERT</strong><br>
        <span style="color: #E0E0E0;">Your score means your business is likely <strong>INVISIBLE</strong> to voice agents.</span>
        </div>
        """, unsafe_allow_html=True)
    elif data['score'] == "N/A":
        st.markdown(f"""
        <div class="blocked-msg">
        <strong>Audit Inconclusive:</strong> This site uses enterprise security or is a Search Engine/Platform.
        </div>
        """, unsafe_allow_html=True)
    
    # 3. DETAILED BREAKDOWN (RESTORED)
    if 'breakdown' in data and data['breakdown']:
        st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Audit Breakdown</h3>", unsafe_allow_html=True)
        for key, val in data['breakdown'].items():
            status_icon = "✅" if val['points'] == val['max'] else "⚠️" if val['points'] > 0 else "❌"
            border_color = "#28A745" if val['points'] == val['max'] else "#FF4B4B"
            
            st.markdown(f"""
            <div style="background-color: #2D3342; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; font-size: 16px;">{status_icon} {key}</div>
                    <div style="font-weight: 700; color: #FFDA47;">{val['points']}/{val['max']}</div>
                </div>
                <div style="color: #B0B0B0; font-size: 14px; margin-top: 5px;">{val['note']}</div>
            </div>
            """, unsafe_allow_html=True)

    # 4. EMAIL FORM
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#FFDA47; font-size:22px; text-align:center; font-weight:700; font-family:Spectral, serif;'>Unlock the detailed PDF breakdown.</p>", unsafe_allow_html=True)
    
    with st.form(key='email_form'):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("Name")
        with c2: email = st.text_input("Email")
        get_pdf = st.form_submit_button("EMAIL ME MY REPORT")

    if get_pdf:
        if name and email:
            save_to_google_sheet(name, email, url, data['score'], data['verdict'])
            st.success("Report Sent!")
            
    # 5. CTA BUTTON
    st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)
    
    # 6. RESET
    c1, c2, c3 = st.columns([1, 1, 1])
    def clear_form():
        st.session_state.audit_data = None
        st.session_state.url_input = ""
    with c2:
        st.button("🔄 START A NEW AUDIT", on_click=clear_form)
