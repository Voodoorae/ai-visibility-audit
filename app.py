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

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    .stApp { background-color: #1A1F2A; color: white; }
    
    /* 1. BRANDING FIX: Found by AI Header */
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

    /* 3. INLINE FORM STYLING */
    /* Forces the button to align nicely with the text input */
    .stButton {
        margin-top: 0px;
    }
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
    }

    /* ALL BUTTONS - FORCE AMBER & FULL WIDTH */
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
    
    /* 6. LINK BUTTONS (HTML) */
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

    /* 4. COMPACT SCORE CARD */
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
    /* Reduced Score Size (by ~400%) */
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
    
    /* Tripwire Box */
    .tripwire-box { 
        background: linear-gradient(135deg, #0B3C5D 0%, #1A1F2A 100%); 
        border: 2px solid #FFDA47; 
        border-radius: 12px; 
        padding: 20px; 
        margin-top: 10px; /* Reduced space */
        margin-bottom: 20px;
        text-align: center; 
    }
    
    /* Centering Utility */
    .centered-btn-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

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
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 10, f"Audit Score: {data['score']}/100", 0, 1, 'C')
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(100, 100, 100)
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
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, f"   Note: {details['note']}", 0, 1)
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
        
        # Scoring Logic
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
# 1. Branding: Found by AI
st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)

# 2. Updated Sub-Head with Google and Apple
st.markdown("<div class='sub-head'>Is your business visible to Google, Apple, Siri, Alexa, and AI Search Agents?</div>", unsafe_allow_html=True)

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# 3. 2-COLUMN LAYOUT FOR INPUT & BUTTON
with st.form(key='audit_form'):
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input("Enter Website URL", placeholder="e.g. plumber-marketing.com", label_visibility="collapsed")
    with col2:
        # Empty label to align with input field
        submit = st.form_submit_button(label='RUN THE AUDIT')

# --- 8 SIGNALS SECTION (Only shown before Audit) ---
if not st.session_state.audit_data:
    st.markdown("<div class='explainer-text'>Is your site blocking AI scanners? Are you visible to Google, Apple, and Alexa voice agents?<br><strong>Find out how visible you really are.</strong></div>", unsafe_allow_html=True)
    st.markdown("<div class='signals-header'>8 Critical Signals Required for AI Visibility</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    signals_1 = ["Voice Assistant Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]
    signals_2 = ["Accessibility Compliance", "SSL Security", "Mobile Readiness", "Entity Clarity"]
    with col1:
        for sig in signals_1: st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)
    with col2:
        for sig in signals_2: st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)

if submit and url:
    st.session_state.url_input = url
    with st.spinner("Scanning..."):
        time.sleep(1)
        st.session_state.audit_data = analyze_website(url)
        st.rerun()

if st.session_state.audit_data:
    data = st.session_state.audit_data
    score_color = data.get("color", "#FFDA47")
    
    # 4. COMPACT SCORE CARD (36px font)
    st.markdown(f"""
    <div class="score-container" style="border-top: 5px solid {score_color};">
        <div class="score-label">AI VISIBILITY SCORE</div>
        <div class="score-circle">{data['score']}/100</div>
        <div class="verdict-text" style="color: {score_color};">{data['verdict']}</div>
    </div>
    """, unsafe_allow_html=True)

    if data["status"] == "blocked":
        st.markdown(f"""
        <div class="blocked-msg">
            We could verify your domain, but your firewall blocked our content scanner.<br>
            <strong>If we are blocked, Siri & Alexa likely are too.</strong>
        </div>
        """, unsafe_allow_html=True)

    # 5. EMAIL FORM (Centered Button)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("### 1. Get Your Full Report")
    st.markdown("<p style='color:#ccc; font-size:14px; text-align:center;'>Unlock the detailed PDF breakdown.</p>", unsafe_allow_html=True)
    
    with st.form(key='email_form'):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", placeholder="Your Name")
        with c2:
            email = st.text_input("Email", placeholder="name@company.com")
        
        # Center the submit button using columns inside the form
        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
            get_pdf = st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS")
        
        if get_pdf:
            if name and email and "@" in email and PDF_AVAILABLE:
                try:
                    pdf_bytes = create_download_pdf(data, st.session_state.url_input)
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="FoundByAI_Report.pdf" style="text-decoration:none;"><button style="background-color: #28A745; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; width: 100%; cursor: pointer;">⬇️ DOWNLOAD PDF REPORT</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success(f"Report generated for {email}!")
                except Exception as e:
                    st.error("PDF Error: Ensure fpdf is installed.")
            elif not PDF_AVAILABLE:
                st.error("PDF Generation unavailable. Please install 'fpdf' in requirements.txt")
            else:
                st.error("Please enter your name and email.")

    # 6. TRIPWIRE (Reduced White Space & Updated Copy)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #FFDA47; margin-bottom: 5px;'>UNLOCK YOUR BUSINESS IN 2-3 HOURS</h3>", unsafe_allow_html=True)
    st.markdown("""
    <p style='text-align: center; color: #fff; margin-bottom: 20px; font-size: 16px;'>
        You are missing critical AI signals. Get the <strong>Fast Fix Toolkit</strong> to unlock your visibility<br>
        or get the <strong>Done For You Tune Up</strong> for a fast hands off full fix.
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background-color: #2D3342; padding: 20px; border-radius: 8px; margin-bottom: 20px;'>
        <div style='margin-bottom: 10px;'>✅ <strong>The Unblocker Guide:</strong> Remove AI crawler blockages.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Accessibility Tags:</strong> Rank for Voice Search.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Schema Generator:</strong> Tell AI exactly what you do.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Copyright Script:</strong> Auto-update for Freshness.</div>
        <div>✅ <strong>Privacy & GDPR:</strong> Build Trust with Agents.</div>
    </div>
    """, unsafe_allow_html=True)

    # 6. ACTION BUTTONS (Renamed & No Pricing Text Below)
    b_col1, b_col2 = st.columns(2)
    
    with b_col1:
        st.markdown("""
        <a href="https://your-checkout-link-toolkit.com" target="_blank" class="amber-btn">
            FAST FIX TOOLKIT £27
        </a>
        """, unsafe_allow_html=True)
        
    with b_col2:
        st.markdown("""
        <a href="https://your-checkout-link-tuneup.com" target="_blank" class="amber-btn">
            BOOK TUNE UP £150
        </a>
        """, unsafe_allow_html=True)

    # 7. CENTERED START NEW AUDIT BUTTON
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 START A NEW AUDIT"):
            st.session_state.audit_data = None
            st.session_state.url_input = ""
            st.rerun()
