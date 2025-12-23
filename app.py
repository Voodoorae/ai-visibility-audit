import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import urllib3
import gspread
from google.oauth2.service_account import Credentials

# Disable SSL warnings for robust scanning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURATION: WEBHOOKS & SHEETS ---
GHL_WEBHOOK_URL = "https://services.leadconnectorhq.com/hooks/8I4dcdbVv5h8XxnqQ9Cg/webhook-trigger/e8d9672c-0b9a-40f6-bc7a-aa93dd78ee99"

# 🔴 CONFIGURATION: YOUR CLEAN SHEET URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KZgBJZFGGeYciI3lgwnxnLe5LwWoJouuqod_ABAag7c" 

# --- GOOGLE SHEETS LOGGING FUNCTION (SILENT MODE) ---
def log_lead_to_sheet(url, score):
    """Silently logs every scan to Google Sheets without alerting the user"""
    try:
        # Load credentials
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Open sheet and append
        sheet = client.open_by_url(SHEET_URL).sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, url, str(score), "Audit Run"])
        
    except Exception as e:
        # Fail silently so the user experience isn't broken
        print(f"⚠️ Logging Error: {e}")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    .stApp { background-color: #1A1F2A; color: white; }
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stHeaderAction"] {display: none !important;}
    
    [data-testid="StyledFullScreenButton"] { display: none !important; }
    [data-testid="stImage"] a { pointer-events: none !important; cursor: default !important; }

    h1 { color: #FFDA47 !important; font-family: 'Spectral', serif !important; font-weight: 800; text-align: center; font-size: 3.5rem; line-height: 1; margin-top: 10px; margin-bottom: 5px; }
    .sub-head { text-align: center; color: #FFFFFF; font-size: 20px; margin-bottom: 25px; font-family: 'Inter', sans-serif; }
    .explainer-text { text-align: center; color: #B0B0B0; font-size: 16px; margin-bottom: 30px; max-width: 600px; margin-left: auto; margin-right: auto; }

    .signal-item { background-color: #2D3342; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: 'Inter', sans-serif; font-size: 14px; color: #E0E0E0; border-left: 3px solid #FFDA47; }

    div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #FFDA47 !important; color: #000000 !important; font-weight: 900 !important; border-radius: 8px !important; height: 50px !important; width: 100%; border: none !important;
    }

    .score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; border: 1px solid #3E4658; }
    .score-circle { font-size: 48px !important; font-weight: 800; color: #FFDA47; font-family: 'Spectral', serif; }
    
    .amber-btn {
        display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; height: 75px; line-height: 1.2; padding-top: 15px; text-decoration: none; text-align: center; font-family: 'Inter', sans-serif; margin-top: 20px; font-size: 18px; text-transform: uppercase; box-shadow: 0 4px 15px rgba(255, 218, 71, 0.3);
    }
    .amber-btn:hover { background-color: #FFFFFF; color: #000000; transform: scale(1.01); transition: 0.2s; }
    </style>
""", unsafe_allow_html=True)

# --- CORE LOGIC ---
def save_lead_to_ghl(name, email, url, score, verdict):
    try:
        payload = {"name": name, "email": email, "website": url, "customData": {"audit_score": score, "audit_verdict": verdict}}
        r = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
        if r.status_code in [200, 201]: st.success(f"Repair plan sent to {email}!")
        else: st.error("Sync error.")
    except: st.error("Connection failed.")

def smart_connect(raw_url):
    raw_url = raw_url.strip()
    clean_url = raw_url.replace("https://", "").replace("http://", "").replace("www.", "")
    attempts = [f"https://{clean_url}", f"https://www.{clean_url}"]
    for url in attempts:
        try:
            r = requests.get(url, headers={'User-Agent': 'FoundByAI/2.0'}, timeout=12, verify=False)
            return r, url
        except: continue
    raise ConnectionError("Failed")

def analyze_website(raw_url):
    try:
        response, working_url = smart_connect(raw_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 25 
        schemas = soup.find_all('script', type='application/ld+json')
        schema_content = "".join([s.string for s in schemas if s.string]).lower()
        if any(x in schema_content for x in ["localbusiness", "organization"]): score += 30
        elif len(schemas) > 0: score += 10
        headers = [h.get_text().lower() for h in soup.find_all(['h1', 'h2', 'h3'])]
        if any(any(q in h for q in ['how','cost','price','best','near']) for h in headers): score += 20
        tag = soup.find('link', rel='canonical')
        if tag and tag.get('href', '').strip().lower().rstrip('/') == working_url.lower().rstrip('/'): score += 10
        if str(datetime.datetime.now().year) in text: score += 7
        if all(img.get('alt') for img in soup.find_all('img')) if soup.find_all('img') else False: score += 8
        
        # FIXED: CEILING TO PREVENT 115% BUG
        final_total = min(score, 100)
        verdict = "AI READY" if final_total >= 85 else ("NEEDS OPTIMIZATION" if final_total >= 55 else "INVISIBLE")
        color = "#28A745" if final_total >= 85 else ("#FFDA47" if final_total >= 55 else "#FF4B4B")
        return {"score": final_total, "verdict": verdict, "color": color}
    except: return {"score": 35, "verdict": "SCAN BLOCKED", "color": "#FFDA47"}

# --- APP LAYOUT ---
st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-head'>Is your business visible to Google, Apple, Siri, Alexa, and AI Agents?</div>", unsafe_allow_html=True)

if "audit_results" not in st.session_state:
    st.markdown("<div class='explainer-text'>AI search agents are replacing traditional search. If your site isn't technically optimized, you're becoming invisible. Run your audit now.</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:800; margin-bottom:15px;'>8 CRITICAL AI SIGNALS</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        for s in ["Voice Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]: st.markdown(f"<div class='signal-item'>✅ {s}</div>", unsafe_allow_html=True)
    with col2:
        for s in ["Accessibility", "SSL Security", "Mobile Readiness", "Entity Clarity"]: st.markdown(f"<div class='signal-item'>✅ {s}</div>", unsafe_allow_html=True)

with st.form("audit_form"):
    url_input = st.text_input("Enter Website URL", placeholder="yourbusiness.com", label_visibility="collapsed")
    submit = st.form_submit_button("RUN THE AUDIT")

if submit and url_input:
    with st.spinner("Analyzing AI Signals..."):
        # 1. Run Analysis
        results = analyze_website(url_input)
        st.session_state.audit_results = results
        st.session_state.current_url = url_input
        
        # 2. LOG TO GOOGLE SHEETS (The Spy Step)
        log_lead_to_sheet(url_input, results['score'])
        
        # 3. Rerun to show results
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

    # 🟢 COPY CHANGE 1: "Get Your Repair Plan"
    st.markdown("<h3 style='text-align:center; color:#FFDA47; margin-top:20px;'>Get Your Repair Plan</h3>", unsafe_allow_html=True)
    
    with st.form("lead_form"):
        c1, c2 = st.columns(2)
        u_name, u_email = c1.text_input("Name"), c2.text_input("Email")
        if st.form_submit_button("SEND REPAIR PLAN"):
            if u_name and u_email: save_lead_to_ghl(u_name, u_email, st.session_state.current_url, res['score'], res['verdict'])
            else: st.error("Please provide name and email.")

    st.markdown("<hr style='border-color: #3E4658;'>", unsafe_allow_html=True)
    
    # 🟢 COPY CHANGE 2: "FIX THIS SCORE"
    st.markdown('<a href="https://go.foundbyai.online/get-toolkit" class="amber-btn">👉 CLICK HERE TO FIX THIS SCORE<br><span style="font-size:14px; font-weight:400;">(Instant Roadmap)</span></a>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style='background-color: #2D3342; padding: 15px; border-radius: 8px; margin-top: 25px; text-align: center; border: 1px solid #3b5998;'>
            <p style='margin-bottom: 5px; color: #FFFFFF;'><strong>Stuck on a technical fix?</strong></p>
            <p style='font-size: 14px; color: #B0B0B0; margin-bottom: 15px;'>Join our community for regular tips and technical tweaks to boost your score.</p>
            <a href="https://www.facebook.com/FoundByAI/" target="_blank" style="color: #FFDA47; text-decoration: none; font-weight: 700; font-size: 16px;">JOIN THE FOUND BY AI COMMUNITY →</a>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 START NEW AUDIT"):
        del st.session_state.audit_results
        st.rerun()
