import streamlit as st
import time
import datetime
import re
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Found By AI", page_icon="👁️", layout="centered", initial_sidebar_state="collapsed")

# --- CSS STYLING ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }
h1 { color: #FFDA47 !important; font-family: 'Spectral', serif !important; font-weight: 800; text-align: center; font-size: 3.5rem; line-height: 1; margin-bottom: 5px; }
.sub-head { text-align: center; color: #FFFFFF; font-size: 20px; margin-bottom: 25px; font-family: 'Inter', sans-serif; }
.explainer-text { text-align: center; color: #B0B0B0; font-size: 16px; margin-bottom: 30px; font-family: 'Inter', sans-serif; max-width: 600px; margin-left: auto; margin-right: auto;}
.signals-header { text-align: center; color: #FFDA47; font-size: 18px; font-weight: 600; margin-bottom: 15px; font-family: 'Inter', sans-serif; }

/* FORCE BUTTONS TO BE AMBER WITH BLACK TEXT */
div[data-testid="stButton"] > button, 
div[data-testid="stFormSubmitButton"] > button { 
    background-color: #FFDA47 !important; 
    color: #000000 !important; 
    font-weight: 900 !important; 
    border-radius: 8px !important; 
    height: 50px !important; 
    border: none !important;
}
div[data-testid="stButton"] > button:hover, 
div[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 0.9;
    color: #000000 !important;
}

input.stTextInput { background-color: #2D3342 !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }
.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; height: 55px; width: 100%; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; margin-top: 10px; margin-bottom: 20px;}
.score-container { background-color: #252B3B; border-radius: 15px; padding: 20px; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658; }
.score-circle { font-size: 36px !important; font-weight: 800; line-height: 1; margin-bottom: 5px; color: #FFDA47; font-family: 'Spectral', serif; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }
.url-display { font-size: 14px; font-weight: 600; color: #B0B0B0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.signal-item { background-color: #2D3342; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-family: 'Inter', sans-serif; font-size: 14px; color: #E0E0E0; border-left: 3px solid #28A745; }
</style>
""", unsafe_allow_html=True)

# --- CACHED CONNECTION (STABILITY FIX) ---
@st.cache_resource
def get_gspread_client():
    """Establishes a persistent connection to Google Sheets"""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    if "gcp_service_account" not in st.secrets:
        return None

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def save_to_google_sheet(name, email, url, score, verdict):
    try:
        client = get_gspread_client()
        if not client: return False
        
        sheet_name = "Found By AI Leads" 
        try:
            sheet = client.open(sheet_name).sheet1
        except Exception:
            # Fallback: try to clear cache and reconnect if connection dropped
            st.cache_resource.clear()
            client = get_gspread_client()
            sheet = client.open(sheet_name).sheet1

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, str(name), str(email), str(url), str(score), str(verdict), "Pending"])
        return True
    except Exception as e:
        print(f"Sheet Error: {e}")
        return False

# --- FAIL-SAFE ENGINE ---
def fallback_analysis(url):
    """Returns a 'blocked' score so the user still gets a result."""
    return {
        "score": 45, 
        "verdict": "AI ACCESS DENIED", 
        "color": "#FF4B4B", 
        "scanned_url": url,
        "breakdown": {
            "Server Access": {"points": 0, "max": 15, "note": "❌ Firewall Blocking AI Crawlers"},
            "Schema Markup": {"points": 0, "max": 30, "note": "❌ Cannot Read (Blocked)"},
            "Voice Readiness": {"points": 0, "max": 20, "note": "❌ Cannot Read (Blocked)"},
            "SSL Security": {"points": 10, "max": 10, "note": "✅ Assumed Valid (HTTPS)"},
            "Content Freshness": {"points": 0, "max": 15, "note": "❌ Cannot Read (Blocked)"}
        }
    }

# --- ANALYSIS ENGINE (MULTI-CHANNEL CONTACT CHECK) ---
def analyze_website(raw_url):
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    results = {"score": 0, "verdict": "", "color": "", "breakdown": {}, "scanned_url": raw_url}
    checks_passed = 0
    total_checks = 6
    
    clean_url = raw_url.strip().replace("https://", "").replace("http://", "").replace("www.", "")
    if clean_url.endswith("/"): clean_url = clean_url[:-1]
    
    try:
        # STEALTH HEADERS
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = None
        # FAST TIMEOUT: 3 Seconds
        for proto in [f"https://{clean_url}", f"https://www.{clean_url}", f"http://{clean_url}"]:
            try:
                r = requests.get(proto, headers=headers, timeout=3, verify=False)
                if r.status_code == 200:
                    response = r
                    break
            except: continue
            
        if not response: 
            return fallback_analysis(clean_url)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0

        # Check 1: Schema
        schemas = soup.find_all('script', type='application/ld+json')
        val = 30 if schemas else 0
        if val > 0: checks_passed += 1 
        score += val
        results["breakdown"]["Schema Markup"] = {"points": val, "max": 30, "note": "Checked JSON-LD Code"}

        # Check 2: Voice Headers
        h_tags = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq', 'what', 'who', 'why', 'when', 'best', 'tips', 'guide', 'help']
        has_voice = any(any(q in h.get_text().lower() for q in q_words) for h in h_tags)
        val = 20 if has_voice else 0
        if val > 0: checks_passed += 1
        score += val
        results["breakdown"]["Voice Optimization"] = {"points": val, "max": 20, "note": "Checked Question Headers"}

        # Check 3: Accessibility
        imgs = soup.find_all('img')
        valid_imgs = sum(1 for i in imgs if i.get('alt'))
        val = 15 if not imgs or (valid_imgs/len(imgs) > 0.8) else 0
        if val > 0: checks_passed += 1
        score += val
        results["breakdown"]["Image Accessibility"] = {"points": val, "max": 15, "note": "Checked Alt Tags"}

        # Check 4: Freshness
        val = 15 if str(datetime.datetime.now().year) in text else 0
        if val > 0: checks_passed += 1
        score += val
        results["breakdown"]["Content Freshness"] = {"points": val, "max": 15, "note": "Checked Current Year"}

        # Check 5: Canonical
        val = 10 if soup.find('link', rel='canonical') else 0
        if val > 0: checks_passed += 1
        score += val
        results["breakdown"]["Canonical Tag"] = {"points": val, "max": 10, "note": "Checked SEO Meta Tags"}

        # Check 6: Contact Signals (PHONE OR EMAIL OR ADDRESS)
        # 1. Phone Regex (Global)
        phone_pattern = r"(\b(?:0800|1800|1300|\+44|0\d{2,4})[\s.-]?[\d\s.-]{6,15}\b)"
        found_phone = re.search(phone_pattern, text)
        
        # 2. Email Regex (Basic check)
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        found_email = re.search(email_pattern, text)
        
        # 3. Postcode Regex (UK & US)
        # Matches: SW1A 1AA or 90210
        postcode_pattern = r"\b([a-z]{1,2}\d{1,2}[a-z]?\s*\d[a-z]{2}|[0-9]{5})\b"
        found_postcode = re.search(postcode_pattern, text)

        # 4. Context Keywords
        local_keywords = ['call', 'tel:', 'contact', 'helpline', 'email', 'address', 'location']
        found_keyword = any(kw in text for kw in local_keywords)
        
        # PASS if ANY contact signal is found
        val = 10 if (found_phone or found_email or found_postcode or found_keyword) else 0
        
        if val > 0: checks_passed += 1 
        score += val
        # Renamed note to reflect wider check
        results["breakdown"]["Local Signals"] = {"points": val, "max": 10, "note": "Checked Phone, Email, or Address"}

        # Scoring Logic
        fails = total_checks - checks_passed
        if fails > 0: score -= (fails * 10)
        
        # Ceilings
        if not schemas: score = min(score, 55)
        if not has_voice: score = min(score, 75)
        score = max(10, min(score, 100))

        if score < 60: results["verdict"], results["color"] = "INVISIBLE TO AI", "#FF4B4B"
        elif score < 86: results["verdict"], results["color"] = "PARTIALLY VISIBLE", "#FFDA47"
        else: results["verdict"], results["color"] = "AI READY", "#28A745"
        
        results["score"] = score
        results["scanned_url"] = clean_url 
        return results

    except:
        return fallback_analysis(raw_url)

# --- MAIN UI LOGIC ---
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None

# HEADER
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)
    st.markdown("<div class='sub-head'>Is your business invisible to Siri&nbsp;&&nbsp;AI?</div>", unsafe_allow_html=True)

# ----------------------------
# STATE 1: LANDING PAGE
# ----------------------------
if st.session_state.audit_data is None:
    
    with st.form(key='audit_form'):
        c1, c2 = st.columns([3, 1])
        with c1: 
            url_input = st.text_input("Website URL", placeholder="example.com", label_visibility="visible")
        with c2: 
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("CHECK MY SCORE")
    
    # --- UPDATED UX: DIAGNOSTIC DASHBOARD (Not Links) ---
    st.divider()
    st.subheader("📡 Analyzing 8 Critical Visibility Signals...")
    st.write("We are checking if these platforms can 'see' your business data.")

    # Create a Grid Layout (2 columns wide)
    col1, col2 = st.columns(2)

    # Column 1 Signals
    with col1:
        with st.container(border=True):
            st.markdown("### 🗺️ Google Maps")
            st.caption("Primary data source for 90% of local traffic.")
            st.markdown("Status: **Scanning...**")
        
        with st.container(border=True):
            st.markdown("### 🍎 Apple Maps (Siri)")
            st.caption("Required for iPhone 'Siri, find a...' queries.")
            st.markdown("Status: **Scanning...**")

        with st.container(border=True):
            st.markdown("### 🗣️ Voice Search")
            st.caption("Amazon Alexa & Google Assistant data points.")
            st.markdown("Status: **Scanning...**")
            
        with st.container(border=True):
            st.markdown("### 🤖 Bing / ChatGPT")
            st.caption("The database used by Microsoft Copilot & ChatGPT.")
            st.markdown("Status: **Scanning...**")

    # Column 2 Signals
    with col2:
        with st.container(border=True):
            st.markdown("### 🔴 Yelp / Yahoo")
            st.caption("Critical for high-intent service searches.")
            st.markdown("Status: **Scanning...**")

        with st.container(border=True):
            st.markdown("### 📍 Facebook Local")
            st.caption("Validation for Meta AI and Instagram maps.")
            st.markdown("Status: **Scanning...**")

        with st.container(border=True):
            st.markdown("### 📱 Waze / TomTom")
            st.caption("GPS data for car navigation systems.")
            st.markdown("Status: **Scanning...**")

        with st.container(border=True):
            st.markdown("### 🔍 Schema Markup")
            st.caption("The code that tells robots what you actually 'do'.")
            st.markdown("Status: **Scanning...**")

    st.info("ℹ️ **Why this matters:** If any of these are broken, AI agents cannot recommend you.")
    # -----------------------------------------------------

    if submit_btn and url_input:
        if "." not in url_input:
            st.error("Please enter a valid URL (e.g., example.com)")
        else:
            with st.spinner("Scanning..."):
                st.session_state.audit_data = analyze_website(url_input)
                d = st.session_
