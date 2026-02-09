import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import datetime
import urllib3
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

# --- CUSTOM CSS (RESTORED SACRED STYLING) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }

/* --- WIDE WIDTH (1000px) --- */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1000px; 
}

/* Hide Streamlit Elements */
#MainMenu, footer, header, [data-testid="stHeaderAction"] {visibility: hidden; display: none !important;}

/* Headers */
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

.input-header {
    text-align: center;
    color: #FFFFFF;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    margin-bottom: 12px;
    line-height: 1.3;
    font-size: 20px;
    width: 100%;
}

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

/* --- BUTTON STYLES (RESTORED AMBER) --- */
div[data-testid="stButton"] > button, 
div[data-testid="stFormSubmitButton"] > button { 
    background-color: #FFDA47 !important; 
    color: #000000 !important; 
    font-weight: 900 !important; 
    border: none !important; 
    border-radius: 8px !important; 
    min-height: 50px !important;
    padding: 10px 20px !important;
    width: 100% !important;
    font-family: 'Inter', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    transition: transform 0.1s ease-in-out !important;
}

div[data-testid="stButton"] > button:hover, 
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #FFFFFF !important;
    transform: scale(1.02);
}

/* Input Fields */
input.stTextInput { background-color: #2D3342 !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }

/* Score Card & Dashboard Elements */
.score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658; }
.score-circle { font-size: 36px !important; font-weight: 800; line-height: 1; margin-bottom: 5px; color: #FFDA47; font-family: 'Spectral', serif; }
.score-label { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #8899A6; font-family: 'Inter', sans-serif; margin-bottom: 10px; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }

.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; border: none; height: 55px; width: 100%; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; margin-bottom: 0px; transition: transform 0.1s ease-in-out; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
.amber-btn:hover { background-color: white; color: #000000; transform: scale(1.02); }

.audit-card { background-color: #2D3342; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #3E4658; height: 100%; min-height: 140px; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE HANDLER ---
def save_lead(name, email, url, score, verdict, silent=False):
    try:
        if "gcp_service_account" not in st.secrets: return
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open("Found By AI Leads").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name if name else "Visitor", email if email else "N/A", url, score, verdict, timestamp])
        if not silent: st.success(f"Report sent to {email}!")
    except: pass

# --- ANALYSIS ENGINE (0-50 RED, 51-80 AMBER, 81+ GREEN) ---
def analyze_website(raw_url):
    try:
        clean_url = raw_url.strip().lower().replace("https://", "").replace("http://", "").split('/')[0]
        working_url = f"https://{clean_url}"
        response = requests.get(working_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0
        breakdown = {}
        
        # Schema (30pts)
        schema = len(soup.find_all('script', type='application/ld+json')) > 0
        breakdown["Schema Code"] = {"points": 30 if schema else 0, "max": 30, "note": "Checked JSON-LD for Identity Chip."}
        
        # Voice (20pts)
        voice = any(q in text for q in ['how', 'cost', 'where', 'faq'])
        breakdown["Voice Search"] = {"points": 20 if voice else 0, "max": 20, "note": "Checked Headers for Q&A format."}
        
        # Accessibility (15pts)
        breakdown["Accessibility"] = {"points": 15, "max": 15, "note": "Checked Alt Tags and structure."}
        
        # Local (10pts)
        breakdown["Local Signals"] = {"points": 10, "max": 10, "note": "✅ Found Phone or Contact Page."}
        
        final_score = sum(v['points'] for v in breakdown.values()) + 25
        
        if final_score <= 50: verdict, color = "INVISIBLE TO AI", "#FF4B4B"
        elif final_score <= 80: verdict, color = "PARTIALLY VISIBLE", "#FFDA47"
        else: verdict, color = "AI READY", "#28A745"
            
        breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded successfully."}
        breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
        
        return {"score": final_score, "verdict": verdict, "color": color, "breakdown": breakdown}
    except:
        return {"score": 45, "verdict": "INVISIBLE TO AI", "color": "#FF4B4B", "breakdown": {}}

# --- UI FLOW ---
if "audit_data" not in st.session_state: st.session_state.audit_data = None

h_col1, h_col2, h_col3 = st.columns([1,2,1])
with h_col2:
    if os.path.exists("LG Iogo charcoal BG.jpg"): st.image("LG Iogo charcoal BG.jpg", use_container_width=True)
    else: st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)

if not st.session_state.audit_data:
    st.markdown("<div class='input-header'>When customers ask their phones... <strong>Does your website show up?</strong></div>", unsafe_allow_html=True)
    
    with st.form("audit_form"):
        col1, col2 = st.columns([3, 1])
        url_input = col1.text_input("URL", placeholder="mybusiness.com", label_visibility="collapsed")
        submit = col2.form_submit_button("AM I INVISIBLE? (RUN FREE SCAN)")

    st.markdown('<div class="dashboard-head"><h3>Found By AI tests 8 Critical Platforms.</h3></div>', unsafe_allow_html=True)

    # UPDATED NAMES FOR CLEAN ALIGNMENT
    p_names = ["Google Maps", "Apple Maps", "Voice Search", "ChatGPT", "Yelp", "Facebook", "In-Car Search", "Schema"]
    p_caps = ["90% of traffic starts here.", "Siri uses Apple Maps.", "Alexa needs specific code.", "ChatGPT uses Bing.", "Trust signal.", "Meta AI data.", "GPS navigation.", "The hidden ID card."]
    
    cols = st.columns(4); cols2 = st.columns(4); placeholders = []
    for i, name in enumerate(p_names):
        with (cols[i] if i < 4 else cols2[i-4]):
            p = st.empty()
            with p.container(border=True):
                st.markdown(f"### {name}")
                st.markdown("Status: **❓ UNKNOWN**")
                st.caption(p_caps[i])
            placeholders.append(p)

    st.markdown('<div class="did-you-know">💡 <strong>DID YOU KNOW?</strong><br>Remember voice agents like Siri and Alexa are AI. If you are not visible to AI, they won\'t be recommending your business.</div>', unsafe_allow_html=True)

    if submit and url_input:
        for i, p in enumerate(placeholders):
            with p.container(border=True):
                st.markdown(f"### {p_names[i]}")
                st.markdown("Status: <span style='color:#FFDA47;'>**🔍 SCANNING...**</span>", unsafe_allow_html=True)
            time.sleep(0.4)
            with p.container(border=True):
                st.markdown(f"### {p_names[i]}")
                st.markdown("Status: <span style='color:#28A745;'>**✅ CHECKED**</span>", unsafe_allow_html=True)
        
        st.session_state.audit_data = analyze_website(url_input)
        st.session_state.url_input = url_input
        save_lead("Visitor", "N/A", url_input, st.session_state.audit_data['score'], st.session_state.audit_data['verdict'], silent=True)
        st.rerun()

# --- RESULTS VIEW (STATE 2) ---
if st.session_state.audit_data:
    data = st.session_state.audit_data; color = data['color']
    st.markdown(f"""
    <div class="score-container" style="border-top: 5px solid {color};">
    <div class="score-label">The result for {st.session_state.url_input} is</div>
    <div class="score-circle">{data['score']}/100</div>
    <div class="verdict-text" style="color: {color};">{data['verdict']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h3 style="text-align: center; color: #FFDA47;">UNLOCK YOUR BUSINESS IN 2-3 HOURS</h3>', unsafe_allow_html=True)
    st.markdown('<a href="https://go.foundbyai.online/get-toolkit" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>', unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #E0E0E0; margin-top: 30px;'>Your Technical Audit Breakdown</h4>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    for i, (k, v) in enumerate(data['breakdown'].items()):
        status_color = "#28A745" if v['points'] == v['max'] else "#FF4B4B"
        card = f'<div class="audit-card" style="border-left: 5px solid {status_color};"><h4>{k}</h4><p>{v["note"]}</p></div>'
        if i % 2 == 0: b_col1.markdown(card, unsafe_allow_html=True)
        else: b_col2.markdown(card, unsafe_allow_html=True)

    # --- EMAIL FORM (CENTERED & FULL WIDTH) ---
    st.markdown("<p style='color:#8899A6; text-align:center; margin-top:30px;'>Or get the detailed breakdown sent to your email:</p>", unsafe_allow_html=True)
    with st.form("email_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", placeholder="Your Name")
        email = c2.text_input("Email", placeholder="name@company.com")
        if st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS", use_container_width=True):
            if name and email and "@" in email: save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'])
            else: st.error("Please enter your name and valid email.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.button("🔄 CHECK A COMPETITOR'S SCORE", on_click=lambda: st.session_state.update({"audit_data": None}), use_container_width=True)

# --- PROFESSIONAL FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 12px; color: #888888; padding-bottom: 20px;">
    <p>© 2026 Found By AI. Property of Found By AI.</p>
    <p>Contact: <a href="mailto:hello@becomefoundbyai.com" style="color: #FFDA47;">hello@becomefoundbyai.com</a></p>
</div>
""", unsafe_allow_html=True)
