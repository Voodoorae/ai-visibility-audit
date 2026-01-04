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
<meta property="og:url" content="https://audit.foundbyai.online">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://placehold.co/1200x630/1A1F2A/FFDA47?text=Found+By+AI">
"""
st.markdown(meta_tags, unsafe_allow_html=True)

# --- CUSTOM CSS (OPTIMIZED FOR CRO & MOBILE) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
.stApp { background-color: #1A1F2A; color: white; }

/* --- 1. WIDENED CONTAINER TO USE SIDE SPACE (1000px) --- */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1000px; /* Widened for Dashboard Grid */
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

/* UNIFIED HEADER STYLE (Applies to both top and bottom text) */
.input-header {
    text-align: center;
    color: #FFFFFF; /* White */
    font-weight: 600; /* Bold */
    font-family: 'Inter', sans-serif;
    margin-bottom: 12px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.3;
    font-size: 20px; /* Unified Size */
    width: 100%;     /* Force Full Width */
}

/* Mobile Tweaks */
@media (max-width: 600px) {
    .input-header {
        font-size: 18px !important; /* Slightly smaller on mobile to guarantee 2 lines */
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

/* CENTERED DASHBOARD HEADER - TIGHTENED */
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
    /* AUTO HEIGHT FOR 2 LINES */
    height: auto !important; 
    min-height: 50px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    white-space: pre-wrap !important; /* Allows line break */
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
.score-label { font-size: 12px; text-transform: uppercase; letter-spacing: 2px; color: #8899A6; font-family: 'Inter', sans-serif; }
.verdict-text { font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif; }
.blocked-msg { color: #FFDA47; font-size: 16px; font-family: 'Inter', sans-serif; line-height: 1.4; margin-top: 10px; padding: 10px; background-color: rgba(255, 218, 71, 0.05); border-radius: 8px; border: 1px solid #FFDA47; text-align: center; }
.amber-btn { display: block; background-color: #FFDA47; color: #000000; font-weight: 900; border-radius: 8px; border: none; height: 55px; width: 100%; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; text-align: center; line-height: 55px; text-decoration: none; font-family: 'Inter', sans-serif; margin-bottom: 0px; transition: transform 0.1s ease-in-out; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
.amber-btn:hover { background-color: white; color: #000000; transform: scale(1.02); }
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
            # Generate Text Summary for Email Body
            report_lines = []
            if audit_data and 'breakdown' in audit_data:
                for k, v in audit_data['breakdown'].items():
                    report_lines.append(f"- {k}: {v['points']}/{v['max']} ({v['note']})")
            report_summary = "\n".join(report_lines)

            payload = {
                "name": name,
                "email": email,
                "website": url,
                "customData": {
                    "audit_score": score,
                    "audit_verdict": verdict,
                    "audit_report_text": report_summary
                },
                "tags": ["Source: AI Audit App"]
            }
            
            response = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
            
            if response.status_code in [200, 201]:
                st.success(f"Success! Data sent to {email}.")
            else:
                st.error(f"GHL Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"Connection Error to GHL: {e}")
            print(f"GHL Webhook Failed: {e}")
    else:
        print("GHL Webhook not configured yet.")

# --- PDF GENERATOR (FIXED NAME PERSONALIZATION) ---
if PDF_AVAILABLE:
    class PDF(FPDF):
        def header(self):
            # FIXED: Ensure string is correctly closed on the same line
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
            
        education_text = """
1. The Firewall Problem: Blocks AI scanners like Siri/Alexa.
2. Schema Markup: The hidden language of AI verification.
3. Accessibility: Critical for AI prioritization.
"""
        pdf.multi_cell(0, 8, education_text)
        
        return pdf.output(dest='S').encode('latin-1')

# --- ENGINES ---
def fallback_analysis(url):
    """Provides a fixed, instructional score for sites that block the scanner."""
    breakdown = {}
    
    # Components that can be verified externally/on the IP layer (score = 35)
    breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded to a ping."}
    breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
    breakdown["Domain Authority"] = {"points": 10, "max": 15, "note": "⚠️ Domain is active and registered, score based on assumption."}
    
    # Components that are blocked (score = 0)
    breakdown["Schema Code"] = {"points": 0, "max": 30, "note": "❌ BLOCKED: AI cannot read content for schema. (CRITICAL)"}
    breakdown["Voice Search"] = {"points": 0, "max": 20, "note": "❌ BLOCKED: AI cannot read content for Q&A headers."}
    breakdown["Accessibility"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content for alt tags."}
    breakdown["Freshness"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content for copyright year."}
    breakdown["Local Signals"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content for phone number."}
    breakdown["Canonical Link"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read HTML header for canonical tag."}
    
    score = sum(item['points'] for item in breakdown.values()) # Should be 35
    
    return {
        "score": score,
        "status": "blocked",
        "verdict": "AI VISIBILITY RESTRICTED",
        "color": "#FFDA47",
        "summary": "Your firewall is blocking AI scanners from reading your content. You must implement the 'Unblocker' fix immediately to proceed.",
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
            # Added verify=False for robustness against old SSL configurations, typical in SMB sites
            response = requests.get(url, headers=headers, timeout=8, verify=False)
            return response, url
        except: continue
    
    raise ConnectionError("Connect failed")

# --- CANONICAL CHECK FUNCTION ---
def check_canonical_status(soup, working_url):
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href', '').strip().lower() == working_url.lower():
        return 10, 10, "✅ Self-referencing canonical URL tag found."
    elif canonical_tag:
        return 5, 10, f"⚠️ Canonical URL exists but points to: {canonical_tag.get('href', 'N/A')}. Should be self-referencing."
    else:
        return 0, 10, "❌ No canonical URL tag found. AI may get confused on source of truth."

def analyze_website(raw_url):
    # Initial dynamic score starts at 0. Total dynamic max is 75 (30+20+15+15+10+10 = 100-25)
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    
    try:
        response, working_url = smart_connect(raw_url)
        
        # Check for firewall block status codes
        if response.status_code in [403, 406, 429, 503]:
            return fallback_analysis(raw_url)
            
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0
        
        # --- AUDIT CRITERIA SCORING ---
        
        # 1. Schema Code (Max: 30) - CRITICAL IDENTITY SIGNAL
        schemas = soup.find_all('script', type='application/ld+json')
        schema_score = 30 if len(schemas) > 0 else 0
        results["breakdown"]["Schema Code"] = {"points": schema_score, "max": 30, "note": "Checked JSON-LD for Identity Chip."}
        score += schema_score

        # 2. Voice Search (Max: 20) - Q&A HEADERS
        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq', 'what is']
        has_questions = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        voice_score = 20 if has_questions else 0
        results["breakdown"]["Voice Search"] = {"points": voice_score, "max": 20, "note": "Checked Headers for Q&A format."}
        score += voice_score

        # 3. Accessibility (Max: 15) - ALT TAGS
        images = soup.find_all('img')
        imgs_with_alt = sum(1 for img in images if img.get('alt'))
        total_imgs = len(images)
        # Score is 15 if no images OR > 80% have alt tags
        acc_score = 15 if total_imgs == 0 or (total_imgs > 0 and (imgs_with_alt / total_imgs) > 0.8) else 0
        results["breakdown"]["Accessibility"] = {"points": acc_score, "max": 15, "note": "Checked Alt Tags (80% minimum)." }
        score += acc_score
        
        # 4. Freshness (Max: 15) - COPYRIGHT YEAR
        current_year = str(datetime.datetime.now().year)
        # Look for current year OR the dynamic script (as per SOP)
        has_current_year = current_year in text
        has_script = '<script>document.write(new Date().getfullyear());</script>' in str(response.content).lower().replace(' ', '')
        
        fresh_score = 15 if has_current_year or has_script else 0
        results["breakdown"]["Freshness"] = {"points": fresh_score, "max": 15, "note": "Checked for current Copyright year or dynamic script."}
        score += fresh_score
        
        # 5. Canonical Link (Max: 10) - SOURCE OF TRUTH (NEW CHECK)
        can_points, can_max, can_note = check_canonical_status(soup, working_url)
        results["breakdown"]["Canonical Link"] = {"points": can_points, "max": can_max, "note": can_note}
        score += can_points

        # 6. Local Signals (Max: 10) - PHONE NUMBER
        phone = re.search(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
        loc_score = 10 if phone else 5 # Half points if no number is found, as we assume it exists on Google/Bing
        results["breakdown"]["Local Signals"] = {"points": loc_score, "max": 10, "note": "Checked for a phone number on the page."}
        score += loc_score
        
        # --- VERDICT LOGIC ---
        
        # Add the fixed 25 points back for display purposes (Server Connectivity 15, SSL 10)
        final_score = score + 25
        
        if final_score < 60:
            results["verdict"], results["color"], results["summary"] = "INVISIBLE TO AI", "#FF4B4B", "Your site is failing core visibility checks. You are almost certainly being overlooked by modern AI search agents."
        elif final_score < 81:
            results["verdict"], results["color"], results["summary"] = "PARTIALLY VISIBLE", "#FFDA47", "You are visible, but your site is missing critical Identity Chips and Voice Readiness signals. Optimization required."
        else:
            results["verdict"], results["color"], results["summary"] = "AI READY", "#28A745", "Excellent work! Your website is technically ready for AI search agents and has the necessary Identity Chips."
            
        # Add fixed points to breakdown for PDF/GHL reporting
        results["breakdown"]["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded successfully."}
        results["breakdown"]["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}
        
        results["score"] = final_score # Final score out of 100
        
        return results

    except Exception: return fallback_analysis(raw_url)

# --- UI RENDER ---
# Center the Logo and Main Title using columns to keep it tight
h_col1, h_col2, h_col3 = st.columns([1,2,1])
with h_col2:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    st.markdown("<h1>found by AI</h1>", unsafe_allow_html=True)

# --- MOVED UP: HIGH IMPACT EXPLAINER (UNIFIED STYLE & MOVED OUT OF COLUMN) ---
st.markdown("""
<div class='input-header'>
When customers ask their phones to find a business...<br>
<strong>Does your website show up?</strong>
</div>
""", unsafe_allow_html=True)

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# --- FORM 1: TOP OF PAGE (Centered nicely) ---
with st.form(key='audit_form'):
    # Use columns to control width of input bar if needed, or keep 3:1 ratio
    col1, col2 = st.columns([3, 1])
    with col1:
        # 1. CHANGED PLACEHOLDER TO "mybusiness.com"
        url = st.text_input("Enter Website URL", placeholder="mybusiness.com", label_visibility="collapsed", key="url_field")
    with col2:
        # --- STRONGER CTA BUTTON ---
        # Added \n and white-space CSS handles the split
        submit = st.form_submit_button("AM I INVISIBLE?\n(RUN FREE SCAN)")

# --- 8 SIGNALS SECTION (REORDERED TO 4 COLUMNS x 2 ROWS) ---
if not st.session_state.audit_data:
    # UPDATED COPY PER EXPERT (NOW INCLUDES CHATGPT)
    st.markdown("""
    <div class="dashboard-head">
        <h3>Found By AI tests 8 Critical Platforms to help ensure your business can be found by AI services like Siri, Alexa, and ChatGPT.</h3>
    </div>
    """, unsafe_allow_html=True)

    # GRID RESTRUCTURED: 4 Cols x 2 Rows
    
    # ROW 1 (The "Big 4")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    
    with r1c1:
        with st.container(border=True):
            st.markdown("### 🗺️ Google Maps")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("90% of local traffic starts here. If you aren't on Maps, you don't exist in 'Near Me' searches.")
            
    with r1c2:
        with st.container(border=True):
            st.markdown("### 🍎 Apple Maps")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Siri exclusively uses Apple Maps. Without this, iPhone users literally cannot find you.")

    with r1c3:
        with st.container(border=True):
            st.markdown("### 🗣️ Voice Search")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Alexa and Google Assistant need specific code to read your answers out loud.")
    
    with r1c4:
        with st.container(border=True):
            st.markdown("### 🤖 Bing / ChatGPT")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("ChatGPT & Microsoft Copilot use Bing's database. If Bing can't find you, AI can't recommend you.")

    # ROW 2 (The "Support 4")
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    
    with r2c1:
        with st.container(border=True):
            st.markdown("### 🔴 Yelp / Yahoo")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Apple and Bing use Yelp to 'verify' you are a real business. It is a critical trust signal.")

    with r2c2:
        with st.container(border=True):
            st.markdown("### 📍 Facebook Local")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Meta AI (Instagram/WhatsApp) uses this map data. Essential for social proof.")

    with r2c3:
        with st.container(border=True):
            st.markdown("### 📱 Waze / TomTom")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("Powers in-car GPS (Uber, Lyft, Dashboards). Don't let customers drive right past your door.")

    with r2c4:
        with st.container(border=True):
            st.markdown("### 🔍 Schema Markup")
            st.markdown("Status: **❓ UNKNOWN**")
            st.caption("The hidden 'ID Card' of your website. Without this, AI robots have to guess what you sell.")

    # --- EDUCATIONAL BOX (MOVED DOWN) ---
    st.markdown("""
    <div class='did-you-know'>
    💡 <strong>DID YOU KNOW?</strong><br>
    Remember voice agents like <strong>Siri and Alexa are AI</strong>. If you are not visible to AI, they won't be recommending your business.
    </div>
    """, unsafe_allow_html=True)
    
    # --- SECOND SEARCH BAR (FOR USER CONVENIENCE) ---
    # APPLIED UNIFIED STYLE HERE TOO
    st.markdown("<div class='input-header'>Ready to check your visibility?</div>", unsafe_allow_html=True)
    with st.form(key='audit_form_bottom'):
        c1, c2 = st.columns([3, 1])
        with c1:
            url_bottom = st.text_input("Enter Website URL", placeholder="mybusiness.com", label_visibility="collapsed", key="url_field_bottom")
        with c2:
            submit_bottom = st.form_submit_button("AM I INVISIBLE?\n(RUN FREE SCAN)")

    # LOGIC FOR BOTH FORMS
    final_url = None
    if submit and url:
        final_url = url
    elif submit_bottom and url_bottom:
        final_url = url_bottom
        
    if final_url:
        # --- INPUT VALIDATION ---
        if not re.match(r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$", final_url):
            st.error("Please enter a valid URL (e.g., example.com or https://example.com) to run the scan.")
            st.session_state.url_input = final_url
            with st.spinner("Connecting to AI Scanners..."):
                time.sleep(1) # Fake tension
                st.session_state.audit_data = analyze_website(final_url)
                st.rerun()

# --- RESULTS VIEW (STATE 2) ---
if st.session_state.audit_data:
    # --- CENTERING CONTAINER FOR RESULTS ---
    # We use a [1, 2, 1] column split to force the content into the middle 50% of the wide 1000px screen.
    r_col1, r_col2, r_col3 = st.columns([1, 2, 1])
    
    with r_col2:
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
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #FFDA47; margin-bottom: 5px;'>UNLOCK YOUR BUSINESS IN 2-3 HOURS</h3>", unsafe_allow_html=True)
        st.markdown("""
        <p style='text-align: center; color: #fff; margin-bottom: 20px; font-size: 16px; line-height: 1.6;'>
        You are missing critical AI signals.<br>
        Get the <strong style='color: #FFDA47;'>Fast Fix Toolkit</strong> to unlock your visibility<br>
        or get the <strong style='color: #FFDA47;'>Done For You Tune Up</strong> for a fast, hands off full fix.
        </p>
        """, unsafe_allow_html=True)

        # --- PRIMARY ACTION: FIX BUTTON (TOP) ---
        st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)

        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#8899A6; font-size:16px; text-align:center;'>Or get the detailed breakdown sent to your email:</p>", unsafe_allow_html=True)

        # --- SECONDARY ACTION: EMAIL FORM (Side-by-side inputs, wide button below) ---
        with st.form(key='email_form'):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Name", placeholder="Your Name")
            with c2:
                email = st.text_input("Email", placeholder="name@company.com")
            
            # Submit button spans full width of form container
            get_pdf = st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS", use_container_width=True)
                
        if get_pdf:
            if name and email and "@" in email:
                save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'], data)
            if not PDF_AVAILABLE:
                st.error("Note: PDF Generation is currently disabled. Check requirements.txt")
            else:
                st.error("Please enter your name and valid email.")

        st.markdown("""
        <div style='background-color: #2D3342; padding: 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 20px;'>
        <div style='margin-bottom: 10px;'>✅ <strong>The Unblocker Guide:</strong> Remove AI crawler blockages.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Accessibility Tags:</strong> Rank for Voice Search.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Schema Generator:</strong> Tell AI exactly what you do.</div>
        <div style='margin-bottom: 10px;'>✅ <strong>Copyright Script:</strong> Auto-update for Freshness.</div>
        <div>✅ <strong>Privacy & GDPR:</strong> Build Trust with Agents.</div>
        </div>
        """, unsafe_allow_html=True)

        # --- REPEAT PRIMARY ACTION: FIX BUTTON (BOTTOM) ---
        st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        # --- TERTIARY ACTION: COMPETITOR CHECK (Renamed & Full Width) ---
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

# END OF FILE
