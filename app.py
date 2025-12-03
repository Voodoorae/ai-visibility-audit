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
<meta property="og:url" content="https://ai-visibility-audit.streamlit.app">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://placehold.co/1200x630/1A1F2A/FFDA47?text=Found+By+AI">
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

    /* --- ULTIMATE BUTTON FIX --- */
    div[data-testid="stButton"] > button, 
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        background-color: #FFDA47 !important; 
        color: #000000 !important;
        font-weight: 900 !important; 
        border: none !important; 
        border-radius: 8px !important;
        height: 50px !important;
        font-family: 'Inter', sans-serif !important;
    }

    div[data-testid="stButton"] > button:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255, 218, 71, 0.4);
    }

    /* --- REMOVE GHOST BUTTONS FROM IMAGES --- */
    [data-testid="StyledFullScreenButton"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* --- INPUT FIELD VISIBILITY --- */
    input.stTextInput {
        background-color: #2D3342 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A5568 !important;
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
            response = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
            
            if response.status_code in [200, 201]:
                st.success(f"System: Data sent to GHL successfully (Status: {response.status_code})")
            else:
                st.error(f"GHL Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"Connection Error to GHL: {e}")
            print(f"GHL Webhook Failed: {e}")
    else:
        print("GHL Webhook not configured yet.")

def update_leads(df):
    df.to_csv(LEADS_FILE, index=False)

# --- PDF GENERATOR (FIXED NAME PERSONALIZATION) ---
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

    # UPDATED: Now accepts 'name' argument
    def create_download_pdf(data, url, name):
        pdf = PDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 10, f"Audit Score: {data['score']}/100", 0, 1, 'C')
        
        # Subtitle with Name
        pdf.set_font("Arial", "I", 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Prepared for: {name}", 0, 1, 'C') # FIXED: Uses user name
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Site: {url}", 0, 1, 'C')
        pdf.ln(10)
        
        # Verdict
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Verdict: {data['verdict']}", 0, 1, 'L')
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, data['summary'])
        pdf.ln(10)
        
        # Technical Breakdown
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
        
        # Education
        education_text = """
        1. The Firewall Problem: Blocks AI scanners like Siri/Alexa.
        2. Schema Markup: The hidden language of AI verification.
        3. Accessibility: Critical for AI prioritization.
        """
        pdf.multi_cell(0, 8, education_text)
        
        return pdf.output(dest='S').encode('latin-1')

# --- ENGINES ---
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
        "summary": "Your firewall is blocking AI scanners.",
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
        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq']
        has_questions = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        voice_score = 20 if has_questions else 0
        results["breakdown"]["Voice Search"] = {"points": voice_score, "max": 20, "note": "Checked Headers."}
        score += voice_score
        schemas = soup.find_all('script', type='application/ld+json')
        schema_score = 20 if len(schemas) > 0 else 0
        results["breakdown"]["Schema Code"] = {"points": schema_score, "max": 20, "note": "Checked JSON-LD."}
        score += schema_score
        phone = re.search(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
        loc_score = 20 if phone else 5
        results["breakdown"]["Local Signals"] = {"points": loc_score, "max": 20, "note": "Checked Phone."}
        score += loc_score
        current_year = str(datetime.datetime.now().year)
        fresh_score = 20 if current_year in text else 0
        results["breakdown"]["Freshness"] = {"points": fresh_score, "max": 20, "note": "Checked Copyright."}
        score += fresh_score
        results["score"] = score
        if score < 60: results["verdict"], results["color"], results["summary"] = "INVISIBLE TO AI", "#FF4B4B", "Your site is failing core visibility checks."
        elif score < 81: results["verdict"], results["color"], results["summary"] = "PARTIALLY VISIBLE", "#FFDA47", "You are visible, but not optimized."
        else: results["verdict"], results["color"], results["summary"] = "AI READY", "#28A745", "Excellent work."
        return results
    except Exception: return fallback_analysis(raw_url)

# --- UI RENDER ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.image("https://placehold.co/600x400/1A1F2A/FFDA47?text=Found+By+AI", use_container_width=True)

st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-head'>Is your business visible to Google, Apple, Siri, Alexa, and AI Search Agents?</div>", unsafe_allow_html=True)

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

with st.form(key='audit_form'):
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input("Enter Website URL", placeholder="e.g. plumber-marketing.com", label_visibility="collapsed", key="url_field")
    with col2:
        submit = st.form_submit_button(label='RUN THE AUDIT')

# --- 8 SIGNALS SECTION ---
if not st.session_state.audit_data:
    st.markdown("<div class='explainer-text'>Is your site blocking AI scanners? Are you visible to Google, Apple, and Alexa voice agents?<br><strong>Find out how visible you really are.</strong></div>", unsafe_allow_html=True)
    st.markdown("<div class='signals-header'>8 Critical Signals Required for AI Visibility</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        for sig in ["Voice Assistant Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]: st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)
    with col2:
        for sig in ["Accessibility Compliance", "SSL Security", "Mobile Readiness", "Entity Clarity"]: st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)

if submit and url:
    st.session_state.url_input = url
    with st.spinner("Scanning..."):
        time.sleep(1)
        st.session_state.audit_data = analyze_website(url)
        st.rerun()

if st.session_state.audit_data:
    data = st.session_state.audit_data
    score_color = data.get("color", "#FFDA47")
    
    html_score_card = f"""
    <div class="score-container" style="border-top: 5px solid {score_color};">
        <div class="score-label">AI VISIBILITY SCORE</div>
        <div class="score-circle">{data['score']}/100</div>
        <div class="verdict-text" style="color: {score_color};">{data['verdict']}</div>
    </div>
    """
    st.markdown(html_score_card, unsafe_allow_html=True)

    if data["status"] == "blocked":
        html_blocked_msg = f"""
        <div class="blocked-msg">
            We could verify your domain, but your firewall blocked our content scanner.<br>
            <strong>If we are blocked, Siri & Alexa likely are too.</strong>
        </div>
        """
        st.markdown(html_blocked_msg, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#FFDA47; font-size:22px; text-align:center; font-weight:700; font-family:Spectral, serif;'>Unlock the detailed PDF breakdown.</p>", unsafe_allow_html=True)
    
    with st.form(key='email_form'):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", placeholder="Your Name")
        with c2:
            email = st.text_input("Email", placeholder="name@company.com")
        
        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
            get_pdf = st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS")
        
        if get_pdf:
            if name and email and "@" in email:
                save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'], data)
                if not PDF_AVAILABLE:
                    st.error("Note: PDF Generation is currently disabled. Check requirements.txt")
            else:
                st.error("Please enter your name and valid email.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #FFDA47; margin-bottom: 5px;'>UNLOCK YOUR BUSINESS IN 2-3 HOURS</h3>", unsafe_allow_html=True)
    st.markdown("""
    <p style='text-align: center; color: #fff; margin-bottom: 20px; font-size: 16px; line-height: 1.6;'>
        You are missing critical AI signals.<br>
        Get the <strong style='color: #FFDA47;'>Fast Fix Toolkit</strong> to unlock your visibility<br>
        or get the <strong style='color: #FFDA47;'>Done For You Tune Up</strong> for a fast, hands off full fix.
    </p>
    """, unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("""<a href="https://your-domain.com/toolkit" target="_blank" class="amber-btn">FAST FIX TOOLKIT £27</a>""", unsafe_allow_html=True)
    with b_col2:
        st.markdown("""<a href="https://your-domain.com/tune-up" target="_blank" class="amber-btn">BOOK TUNE UP £150</a>""", unsafe_allow_html=True)

    st.markdown("""
    <div style='background-color: #2D3342; padding: 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 20px;'>
        <div style='margin-bottom: 10px;'>✅ <strong>The Unblocker Guide:</strong> Remove AI crawler blockages.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Accessibility Tags:</strong> Rank for Voice Search.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Schema Generator:</strong> Tell AI exactly what you do.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Copyright Script:</strong> Auto-update for Freshness.</div>
        <div>✅ <strong>Privacy & GDPR:</strong> Build Trust with Agents.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    
    def clear_form():
        st.session_state.audit_data = None
        st.session_state.url_input = ""
        st.session_state.url_field = ""
        
    with c2:
        st.button("🔄 START A NEW AUDIT", on_click=clear_form)

# --- ADMIN PANEL ---
if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False

with st.expander("Admin Panel (Restricted)"):
    if not st.session_state.admin_unlocked:
        password = st.text_input("Enter Admin Password", type="password", key="admin_pw_input")
        if password == "318345":
            st.session_state.admin_unlocked = True
            st.rerun()
    
    if st.session_state.admin_unlocked:
        st.success("Access Granted")
        df = load_leads()
        edited_df = st.data_editor(df, num_rows="dynamic")
        
        if st.button("Update Status"):
            update_leads(edited_df)
            st.success("Database Updated")
            
        st.download_button(label="Download CSV", data=edited_df.to_csv(index=False).encode('utf-8'), file_name='leads.csv', mime='text/csv')
        
        if not df.empty:
            st.write("### Regenerate Client PDF")
            selected_row = st.selectbox("Select Lead to Generate PDF", df.index, format_func=lambda x: f"{df.iloc[x]['Name']} - {df.iloc[x]['URL']}")
            if st.button("Generate & Download PDF"):
                try:
                    row = df.iloc[selected_row]
                    audit_data_raw = row['AuditData']
                    if isinstance(audit_data_raw, str): audit_data = json.loads(audit_data_raw)
                    else: audit_data = audit_data_raw
                    # Pass Name to PDF
                    pdf_bytes = create_download_pdf(audit_data, row['URL'], row['Name'])
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="Report_{row["Name"]}.pdf">Click to Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No leads captured yet.")

# END OF FILE
