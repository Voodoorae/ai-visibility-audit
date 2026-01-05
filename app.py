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

# --- SOCIAL META TAGS ---
meta_tags = """
<meta property="og:title" content="Found By AI - Visibility Audit">
<meta property="og:description" content="Is your business invisible to Siri, Alexa & Google? Check your AI Visibility Score now.">
<meta property="og:image" content="https://placehold.co/1200x630/1A1F2A/FFDA47?text=Found+By+AI">
<meta property="og:url" content="https://audit.foundbyai.online">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://placehold.co/1200x630/1A1F2A/FFDA47?text=Found+By+AI">
"""
st.markdown(meta_tags, unsafe_allow_html=True)

# --- CUSTOM CSS (YOUR EXACT ORIGINAL STYLING) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }

/* --- 1. WIDE WIDTH (1000px) --- */
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

/* Headers - TIGHTENED */
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
    color: #FFFFFF; /* White */
    font-weight: 600; /* Bold */
    font-family: 'Inter', sans-serif;
    margin-bottom: 12px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.3;
    font-size: 20px;
    width: 100%;
}

/* Mobile Tweaks */
@media (max-width: 600px) {
    .input-header {
        font-size: 18px !important;
        padding-left: 5px;
        padding-right: 5px;
    }
    h1 {
        font-size: 2.5rem !important;
    }
}

/* THE CARRIE BOX */
.did-you-know { 
    text-align: center; 
    color: #E0E0E0; 
    font-size: 16px; 
    margin-top: 25px; 
    margin-bottom: 25px; 
    font-family: 'Inter', sans-serif; 
    font-weight: 500; 
    background: #2D3342; 
    padding: 15px; 
    border-radius: 8px; 
    border: 1px solid #4A5568; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
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
    line-height: 1.4;
}

/* --- BUTTON STYLES --- */
div[data-testid="stButton"] > button, 
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button { 
    background-color: #FFDA47 !important; 
    color: #000000 !important; 
    font-weight: 900 !important; 
    border: none !important; 
    border-radius: 8px !important; 
    height: auto !important; 
    min-height: 50px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    white-space: pre-wrap !important;
    line-height: 1.2 !important;
    font-family: 'Inter', sans-serif !important;
    opacity: 1 !important;
}
div[data-testid="stButton"] > button:hover, 
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(255, 218, 71, 0.4);
}

/* --- INPUT & MISC --- */
[data-testid="StyledFullScreenButton"], [data-testid="stImage"] a[target="_blank"] { display: none !important; visibility: hidden !important; }
input.stTextInput { background-color: #2D3342 !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }

/* Score Card & Dashboard Elements */
.score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658; }
.score-circle { font-size: 36px !important; font-weight: 800; line-height: 1; margin-bottom: 5px; color: #FFDA47; font-family: 'Spectral', serif; }
.score-label { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #8899A6; font-family: 'Inter', sans-serif; margin-bottom: 10px; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }
.blocked-msg { color: #FFDA47; font-size: 16px; font-family: 'Inter', sans-serif; line-height: 1.4; margin-top: 10px; padding: 10px; background-color: rgba(255, 218, 71, 0.05); border-radius: 8px; border: 1px solid #FFDA47; text-align: center; }
.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; border: none; height: 55px; width: 100%; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; margin-bottom: 0px; transition: transform 0.1s ease-in-out; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
.amber-btn:hover { background-color: white; color: #000000; transform: scale(1.02); }

/* --- CARD STYLE FOR BREAKDOWN --- */
.audit-card {
    background-color: #2D3342;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #3E4658;
    height: 100%;
}
.audit-card h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    color: #FFFFFF;
}
.audit-card p {
    margin: 5px 0 0 0;
    font-size: 14px;
    color: #B0B3B8;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE / GOOGLE SHEETS HANDLER (REPLACES WEBHOOK) ---
def save_lead(name, email, url, score, verdict, audit_data):
    try:
        if "gcp_service_account" not in st.secrets:
            # We don't crash, we just warn if secrets are missing
            st.warning("Data connection missing. Please check secrets.")
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
        print(f"Sheet Error: {e}")
        st.warning("We generated your report, but couldn't save to the database.")

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
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, f"    Note: {details['note']}", 0, 1)
            pdf.ln(10)
        return pdf.output(dest='S').encode('latin-1')

# --- ENGINES (BULLETPROOF URL HANDLING) ---
def fallback_analysis(url):
    breakdown = {}
    breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded to a ping."}
    breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
    breakdown["Domain Authority"] = {"points": 10, "max": 15, "note": "⚠️ Domain is active and registered, score based on assumption."}
    breakdown["Schema Code"] = {"points": 0, "max": 30, "note": "❌ BLOCKED: AI cannot read content for schema."}
    breakdown["Voice Search"] = {"points": 0, "max": 20, "note": "❌ BLOCKED: AI cannot read content for Q&A."}
    breakdown["Accessibility"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content for alt tags."}
    breakdown["Freshness"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content for copyright."}
    breakdown["Local Signals"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content for phone."}
    breakdown["Canonical Link"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read HTML header."}
    score = sum(item['points'] for item in breakdown.values())
    return {
        "score": score,
        "status": "blocked",
        "verdict": "AI VISIBILITY RESTRICTED",
        "color": "#FFDA47",
        "summary": "Your firewall is blocking AI scanners from reading your content. You must implement the 'Unblocker' fix immediately to proceed.",
        "breakdown": breakdown
    }

def smart_connect(raw_url):
    clean_url = raw_url.strip().lower()
    clean_url = clean_url.replace("https://", "").replace("http://", "")
    if clean_url.startswith("www."): clean_url = clean_url[4:]
    if clean_url.endswith("/"): clean_url = clean_url[:-1]
    
    targets = [
        f"https://www.{clean_url}",
        f"https://{clean_url}",
        f"http://www.{clean_url}",
        f"http://{clean_url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/'
    }
    
    for target in targets:
        try:
            response = requests.get(target, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                return response, target
        except:
            continue 
    raise ConnectionError("Connect failed")

def check_canonical_status(soup, working_url):
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href', '').strip().lower() == working_url.lower():
        return 10, 10, "✅ Self-referencing canonical URL tag found."
    elif canonical_tag:
        return 5, 10, f"⚠️ Canonical URL exists but points to: {canonical_tag.get('href', 'N/A')}. Should be self-referencing."
    else:
        return 0, 10, "❌ No canonical URL tag found. AI may get confused on source of truth."

def analyze_website(raw_url):
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    try:
        response, working_url = smart_connect(raw_url)
        if response.status_code in [403, 406, 429, 503]:
            return fallback_analysis(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0
        
        # 1. Schema Code (Max INCREASED to 40 to balance score)
        schemas = soup.find_all('script', type='application/ld+json')
        schema_score = 40 if len(schemas) > 0 else 0
        results["breakdown"]["Schema Code"] = {"points": schema_score, "max": 40, "note": "Checked JSON-LD for Identity Chip."}
        score += schema_score

        # 2. Voice Search (Max: 20)
        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq', 'what is']
        has_questions = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        voice_score = 20 if has_questions else 0
        results["breakdown"]["Voice Search"] = {"points": voice_score, "max": 20, "note": "Checked Headers for Q&A format."}
        score += voice_score

        # 3. Accessibility (Max REDUCED to 5 so failure penalty is small)
        images = soup.find_all('img')
        imgs_with_alt = sum(1 for img in images if img.get('alt'))
        total_imgs = len(images)
        acc_score = 5 if total_imgs == 0 or (total_imgs > 0 and (imgs_with_alt / total_imgs) > 0.8) else 0
        results["breakdown"]["Accessibility"] = {"points": acc_score, "max": 5, "note": "Checked Alt Tags (80% minimum)." }
        score += acc_score
        
        # 4. Freshness (Max: 15)
        current_year = str(datetime.datetime.now().year)
        has_current_year = current_year in text
        has_script = '<script>document.write(new Date().getfullyear());</script>' in str(response.content).lower().replace(' ', '')
        fresh_score = 15 if has_current_year or has_script else 0
        results["breakdown"]["Freshness"] = {"points": fresh_score, "max": 15, "note": "Checked for current Copyright year or dynamic script."}
        score += fresh_score
        
        # 5. Canonical Link (Max: 10)
        can_points, can_max, can_note = check_canonical_status(soup, working_url)
        results["breakdown"]["Canonical Link"] = {"points": can_points, "max": can_max, "note": can_note}
        score += can_points

        # 6. Local Signals (Max: 10)
        phone_pattern = r"(\+\d{1,3}\s?)?\(?\d{2,5}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}"
        phone = re.search(phone_pattern, text)
        has_contact = "contact" in text or soup.find('a', href=re.compile(r'contact', re.I))
        
        if phone or has_contact:
            loc_score = 10
            note = "✅ Found Phone Number or Contact Page."
        else:
            loc_score = 5
            note = "⚠️ No Phone or Contact link found."
            
        results["breakdown"]["Local Signals"] = {"points": loc_score, "max": 10, "note": note}
        score += loc_score
        
        # Final Score Calculation (No padding)
        final_score = score
        
        if final_score < 60:
            results["verdict"], results["color"], results["summary"] = "INVISIBLE TO AI", "#FF4B4B", "Your site is failing core visibility checks. You are almost certainly being overlooked by modern AI search agents."
        elif final_score < 81:
            results["verdict"], results["color"], results["summary"] = "PARTIALLY VISIBLE", "#FFDA47", "You are visible, but your site is missing critical Identity Chips and Voice Readiness signals. Optimization required."
        else:
            results["verdict"], results["color"], results["summary"] = "AI READY", "#28A745", "Excellent work! Your website is technically ready for AI search agents and has the necessary Identity Chips."
            
        results["breakdown"]["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded successfully."}
        results["breakdown"]["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
        results["score"] = final_score
        return results

    except Exception: return fallback_analysis(raw_url)

# --- UI RENDER (EXACT LAYOUT RECONSTRUCTION) ---
h_col1, h_col2, h_col3 = st.columns([1,2,1])
with h_col2:
    # UPDATED LOGO HANDLING TO MATCH YOUR FILE
    if os.path.exists("LG Iogo charcoal BG.jpg"):
        st.image("LG Iogo charcoal BG.jpg", use_container_width=True)
    else:
        st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# --- LANDING PAGE VIEW ---
if not st.session_state.audit_data:
    st.markdown("""
    <div class='input-header'>
    When customers ask their phones to find a business...<br>
    <strong>Does your website show up?</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key='audit_form'):
        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input("Enter Website URL", placeholder="mybusiness.com", label_visibility="collapsed", key="url_field")
        with col2:
            submit = st.form_submit_button("AM I INVISIBLE?\n(RUN FREE SCAN)")

    st.markdown("""
    <div class="dashboard-head">
        <h3>Found By AI tests 8 Critical Platforms to help ensure your business can be found by AI services like Siri, Alexa, and ChatGPT.</h3>
    </div>
    """, unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        with st.container(border=True):
            st.markdown("### 🗺️ Google Maps")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("90% of local traffic starts here.")
    with r1c2:
        with st.container(border=True):
            st.markdown("### 🍎 Apple Maps")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Siri exclusively uses Apple Maps.")
    with r1c3:
        with st.container(border=True):
            st.markdown("### 🗣️ Voice Search")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Alexa and Google Assistant need specific code.")
    with r1c4:
        with st.container(border=True):
            st.markdown("### 🤖 Bing / ChatGPT")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("ChatGPT & Copilot use Bing's database.")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        with st.container(border=True):
            st.markdown("### 🔴 Yelp / Yahoo")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Critical verification and trust signal.")
    with r2c2:
        with st.container(border=True):
            st.markdown("### 📍 Facebook Local")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Meta AI uses this map data.")
    with r2c3:
        with st.container(border=True):
            st.markdown("### 📱 Waze / TomTom")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Powers in-car GPS navigation.")
    with r2c4:
        with st.container(border=True):
            st.markdown("### 🔍 Schema Markup")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("The hidden 'ID Card' of your website.")

    st.markdown("""
    <div class='did-you-know'>
    💡 <strong>DID YOU KNOW?</strong><br>
    Remember voice agents like <strong>Siri and Alexa are AI</strong>. If you are not visible to AI, they won't be recommending your business.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='input-header'>Ready to check your visibility?</div>", unsafe_allow_html=True)
    with st.form(key='audit_form_bottom'):
        c1, c2 = st.columns([3, 1])
        with c1:
            url_bottom = st.text_input("Enter Website URL", placeholder="mybusiness.com", label_visibility="collapsed", key="url_field_bottom")
        with c2:
            submit_bottom = st.form_submit_button("AM I INVISIBLE?\n(RUN FREE SCAN)")

    final_url = None
    if submit:
        if not url: st.error("Please enter a website URL to scan.")
        else: final_url = url
    elif submit_bottom:
        if not url_bottom: st.error("Please enter a website URL to scan.")
        else: final_url = url_bottom
        
    if final_url:
        if not re.match(r"^(https?:\/\/)?(www\.)?[\w-]+\.[\w.-]+(\/.*)?$", final_url.strip()):
             st.error("Please enter a valid URL (e.g., example.com or https://example.com) to run the scan.")
        else:
            st.session_state.url_input = final_url
            with st.spinner("Connecting to AI Scanners..."):
                time.sleep(1)
                st.session_state.audit_data = analyze_website(final_url)
                st.rerun()

# --- RESULTS VIEW (STATE 2) ---
if st.session_state.audit_data:
    data = st.session_state.audit_data
    score_color = data.get("color", "#FFDA47")

    # 1. SCORE CARD (FULL 1000px WIDTH)
    html_score_card = f"""
    <div class="score-container" style="border-top: 5px solid {score_color};">
    <div class="score-label">The result for {st.session_state.url_input} is</div>
    <div class="score-circle">{data['score']}/100</div>
    <div class="verdict-text" style="color: {score_color};">{data['verdict']}</div>
    </div>
    """
    st.markdown(html_score_card, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # 2. HEADLINE
    st.markdown("<h3 style='text-align: center; color: #FFDA47; margin-bottom: 5px;'>UNLOCK YOUR BUSINESS IN 2-3 HOURS</h3>", unsafe_allow_html=True)

    # 3. FIX BUTTON #1 (SANDWICH TOP)
    st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)

    # 4. BREAKDOWN CARDS (SANDWICH FILLING)
    st.markdown("<h4 style='text-align: center; color: #E0E0E0; margin-bottom: 20px; margin-top: 30px;'>Your Technical Audit Breakdown</h4>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    items = list(data['breakdown'].items())
    for idx, (k, v) in enumerate(items):
        is_pass = v['points'] == v['max']
        status_color = "#28A745" if is_pass else "#FF4B4B"
        icon_text = "PASS" if is_pass else "FAIL"
        
        card_html = f"""
        <div class="audit-card" style="border-left: 5px solid {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0; color: white;">{k}</h4>
                <span style="background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">{icon_text}</span>
            </div>
            <p style="margin: 0; font-size: 14px; color: #B0B3B8;">{v['note']}</p>
        </div>
        """
        
        if idx % 2 == 0:
            with b_col1: st.markdown(card_html, unsafe_allow_html=True)
        else:
            with b_col2: st.markdown(card_html, unsafe_allow_html=True)
            
    if data["status"] == "blocked":
        html_blocked_msg = f"""
        <div class="blocked-msg">
        We could verify your domain, but your firewall blocked our content scanner.<br>
        <strong>If we are blocked, Siri & Alexa likely are too.</strong>
        </div>
        """
        st.markdown(html_blocked_msg, unsafe_allow_html=True)

    # 5. FIX BUTTON #2 (SANDWICH BOTTOM)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    
    # 6. EMAIL FORM (DOWNSELL)
    st.markdown("<p style='color:#8899A6; font-size:16px; text-align:center;'>Or get the detailed breakdown sent to your email:</p>", unsafe_allow_html=True)
    with st.form(key='email_form'):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", placeholder="Your Name")
        with c2:
            email = st.text_input("Email", placeholder="name@company.com")
        
        get_pdf = st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS", use_container_width=True)
            
    if get_pdf:
        if name and email and "@" in email:
            save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'], data)
        else:
            st.error("Please enter your name and valid email.")

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # 7. COMPETITOR BUTTON
    def clear_form():
        st.session_state.audit_data = None
        st.session_state.url_input = ""
        
    st.button("🔄 CHECK A COMPETITOR'S SCORE", on_click=clear_form, use_container_width=True)

# --- PROFESSIONAL FOOTER (GLOBAL) ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 12px; color: #888888; padding-bottom: 20px; font-family: 'Inter', sans-serif;">
    <p>© 2026 Found By AI. All rights reserved.<br>
    Property of Found By AI.</p>
    <p>Your privacy is important to us. We do not sell your data.</p>
    <p>Contact: <a href="mailto:hello@becomefoundbyai.com" style="color: #FFDA47; text-decoration: none;">hello@becomefoundbyai.com</a></p>
</div>
""", unsafe_allow_html=True)
