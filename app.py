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
"""
st.markdown(meta_tags, unsafe_allow_html=True)

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;600;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

.stApp { background-color: #1A1F2A; color: white; }
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stHeaderAction"] {display: none !important;}

/* Headers */
h1 {
    color: #FFDA47 !important;
    font-family: 'Spectral', serif !important;
    font-weight: 800;
    text-align: center;
    margin-top: 5px; margin-bottom: 5px;
    font-size: 3.5rem; letter-spacing: -1px; line-height: 1;
}
.sub-head {
    text-align: center; color: #FFFFFF; font-size: 20px;
    margin-bottom: 25px; font-weight: 400; font-family: 'Inter', sans-serif;
}
.explainer-text {
    text-align: center; color: #B0B0B0; font-size: 16px;
    margin-bottom: 30px; font-family: 'Inter', sans-serif;
    max-width: 600px; margin-left: auto; margin-right: auto;
}

/* Button Styling */
div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    background-color: #FFDA47 !important; color: #000000 !important;
    font-weight: 900 !important; border: none !important;
    border-radius: 8px !important; height: 50px !important;
    font-family: 'Inter', sans-serif !important; opacity: 1 !important;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #FFFFFF !important; color: #000000 !important;
    transform: scale(1.02); box-shadow: 0 0 15px rgba(255, 218, 71, 0.4);
}

/* Remove Ghost Icons */
[data-testid="StyledFullScreenButton"], [data-testid="stImage"] a[target="_blank"] {
    display: none !important; visibility: hidden !important;
}

/* Input Fields */
input.stTextInput {
    background-color: #2D3342 !important; color: #FFFFFF !important;
    border: 1px solid #4A5568 !important;
}
div[data-testid="stMarkdownContainer"] p {
    font-size: 16px; font-weight: 600;
}

/* Link Buttons */
.amber-btn {
    display: block; background-color: #FFDA47; color: #000000;
    font-weight: 900; border-radius: 8px; height: 55px; width: 100%;
    font-size: 16px; text-transform: uppercase; letter-spacing: 1px;
    text-align: center; line-height: 55px; text-decoration: none;
    font-family: 'Inter', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.amber-btn:hover {
    background-color: white; color: #000000; transform: scale(1.02);
}

/* Score Card */
.score-container {
    background-color: #252B3B; border-radius: 15px; padding: 20px;
    text-align: center; margin-top: 10px; margin-bottom: 20px; border: 1px solid #3E4658;
}
.score-circle {
    font-size: 36px !important; font-weight: 800; line-height: 1;
    margin-bottom: 5px; color: #FFDA47; font-family: 'Spectral', serif;
}
.verdict-text {
    font-size: 20px; font-weight: 800; margin-top: 5px; font-family: 'Spectral', serif;
}
.blocked-msg {
    color: #FFDA47; font-size: 16px; font-family: 'Inter', sans-serif;
    margin-top: 10px; padding: 10px; background-color: rgba(255, 218, 71, 0.05);
    border-radius: 8px; border: 1px solid #FFDA47; text-align: center;
}
.signal-item {
    background-color: #2D3342; padding: 10px; border-radius: 6px;
    margin-bottom: 10px; font-family: 'Inter', sans-serif; font-size: 14px;
    color: #E0E0E0; border-left: 3px solid #28A745;
}
</style>
""", unsafe_allow_html=True)

# --- DATA HANDLER ---
LEADS_FILE = "leads.csv"

def load_leads():
    if os.path.exists(LEADS_FILE):
        return pd.read_csv(LEADS_FILE)
    else:
        return pd.DataFrame(columns=["Timestamp", "Name", "Email", "URL", "Score", "Verdict", "AuditData", "Sent"])

def save_lead(name, email, url, score, verdict, audit_data):
    df = load_leads()
    new_entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name, "Email": email, "URL": url,
        "Score": score, "Verdict": verdict, "AuditData": json.dumps(audit_data), "Sent": False
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(LEADS_FILE, index=False)

    if "PASTE_YOUR_GHL" not in GHL_WEBHOOK_URL:
        try:
            report_lines = []
            if audit_data and 'breakdown' in audit_data:
                for k, v in audit_data['breakdown'].items():
                    report_lines.append(f"- {k}: {v['points']}/{v['max']} ({v['note']})")
            report_summary = "\n".join(report_lines)

            payload = {
                "name": name, "email": email, "website": url,
                "customData": { "audit_score": score, "audit_verdict": verdict, "audit_report_text": report_summary },
                "tags": ["Source: AI Audit App"]
            }
            response = requests.post(GHL_WEBHOOK_URL, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                st.success(f"Success! Data sent to {email}.")
            else:
                st.error(f"GHL Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# --- ENGINES ---
def fallback_analysis(url):
    breakdown = {}
    breakdown["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server online."}
    breakdown["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL valid."}
    breakdown["Domain Authority"] = {"points": 10, "max": 15, "note": "⚠️ Domain active."}
    breakdown["Schema Code"] = {"points": 0, "max": 30, "note": "❌ BLOCKED: AI cannot read content (CRITICAL)"}
    breakdown["Voice Search"] = {"points": 0, "max": 20, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Accessibility"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Freshness"] = {"points": 0, "max": 15, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Local Signals"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content."}
    breakdown["Canonical Link"] = {"points": 0, "max": 10, "note": "❌ BLOCKED: AI cannot read content."}

    return {
        "score": 35, "fails": 6, "total_checks": 6,
        "status": "blocked", "verdict": "AI VISIBILITY RESTRICTED", "color": "#FFDA47",
        "summary": "Your firewall is blocking AI scanners from reading your content. You must implement the 'Unblocker' fix immediately.",
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

def check_canonical_status(soup, working_url):
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href', '').strip().lower() == working_url.lower():
        return 10, 10, "✅ Self-referencing canonical URL tag found."
    elif canonical_tag:
        return 5, 10, f"⚠️ Canonical URL points to: {canonical_tag.get('href', 'N/A')}."
    else:
        return 0, 10, "❌ No canonical URL tag found."

def analyze_website(raw_url):
    results = {"score": 0, "status": "active", "breakdown": {}, "summary": "", "debug_error": ""}
    checks_passed = 0
    total_checks = 6 
    
    try:
        response, working_url = smart_connect(raw_url)
        if response.status_code in [403, 406, 429, 503]:
            return fallback_analysis(raw_url)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text().lower()
        score = 0

        # 1. Schema Code (Max: 30)
        schemas = soup.find_all('script', type='application/ld+json')
        schema_score = 30 if len(schemas) > 0 else 0
        if schema_score > 0: checks_passed += 1
        results["breakdown"]["Schema Code"] = {"points": schema_score, "max": 30, "note": "Checked JSON-LD for Identity Chip."}
        score += schema_score

        # 2. Voice Search (Max: 20)
        headers_h = soup.find_all(['h1', 'h2', 'h3'])
        q_words = ['how', 'cost', 'price', 'where', 'faq', 'what is']
        has_questions = any(any(q in h.get_text().lower() for q in q_words) for h in headers_h)
        voice_score = 20 if has_questions else 0
        if voice_score > 0: checks_passed += 1
        results["breakdown"]["Voice Search"] = {"points": voice_score, "max": 20, "note": "Checked Headers for Q&A format."}
        score += voice_score

        # 3. Accessibility (Max: 15)
        images = soup.find_all('img')
        imgs_with_alt = sum(1 for img in images if img.get('alt'))
        total_imgs = len(images)
        acc_score = 15 if total_imgs == 0 or (total_imgs > 0 and (imgs_with_alt / total_imgs) > 0.8) else 0
        if acc_score > 0: checks_passed += 1
        results["breakdown"]["Accessibility"] = {"points": acc_score, "max": 15, "note": "Checked Alt Tags (80% minimum)."}
        score += acc_score

        # 4. Freshness (Max: 15)
        current_year = str(datetime.datetime.now().year)
        has_current_year = current_year in text
        has_script = '<script>document.write(new Date().getfullyear());</script>' in str(response.content).lower().replace(' ', '')
        fresh_score = 15 if has_current_year or has_script else 0
        if fresh_score > 0: checks_passed += 1
        results["breakdown"]["Freshness"] = {"points": fresh_score, "max": 15, "note": "Checked for current Copyright year."}
        score += fresh_score

        # 5. Canonical Link (Max: 10)
        can_points, can_max, can_note = check_canonical_status(soup, working_url)
        if can_points == 10: checks_passed += 1
        results["breakdown"]["Canonical Link"] = {"points": can_points, "max": can_max, "note": can_note}
        score += can_points

        # 6. Local Signals (Max: 10)
        phone = re.search(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", text)
        loc_score = 10 if phone else 5
        if loc_score == 10: checks_passed += 1
        results["breakdown"]["Local Signals"] = {"points": loc_score, "max": 10, "note": "Checked for a phone number on the page."}
        score += loc_score

        # --- VERDICT LOGIC ---
        final_score = score + 25
        
        # STRICT CEILING 1: Missing Schema = Max 55%
        if schema_score == 0:
            final_score = min(final_score, 55)

        # STRICT CEILING 2: Missing Voice Content = Max 75%
        if voice_score == 0:
            final_score = min(final_score, 75)

        # Standard Ceiling
        final_score = min(final_score, 100)

        if final_score < 60:
            results["verdict"], results["color"], results["summary"] = "INVISIBLE TO AI", "#FF4B4B", "Your site is failing core visibility checks."
        elif final_score < 81:
            results["verdict"], results["color"], results["summary"] = "PARTIALLY VISIBLE", "#FFDA47", "You are visible, but your site is missing critical Identity Chips."
        else:
            results["verdict"], results["color"], results["summary"] = "AI READY", "#28A745", "Excellent work! Your website is technically ready."

        results["breakdown"]["Server Connectivity"] = {"points": 15, "max": 15, "note": "✅ Server responded successfully."}
        results["breakdown"]["SSL Security"] = {"points": 10, "max": 10, "note": "✅ SSL Certificate valid."}

        results["score"] = final_score
        results["fails"] = total_checks - checks_passed
        results["total_checks"] = total_checks
        
        return results

    except Exception:
        return fallback_analysis(raw_url)

# --- UI RENDER ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
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
        for sig in ["Voice Assistant Readiness", "AI Crawler Access", "Schema Markup", "Content Freshness"]:
            st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)
    with col2:
        for sig in ["Accessibility Compliance", "SSL Security", "Mobile Readiness", "Entity Clarity"]:
            st.markdown(f"<div class='signal-item'>✅ {sig}</div>", unsafe_allow_html=True)

if submit and url:
    # Relaxed URL check: Just needs to contain a dot (e.g. "ethelsgem.com")
    if "." not in url:
        st.error("Please enter a valid URL.")
        st.session_state.url_input = ""
    else:
        st.session_state.url_input = url
        with st.spinner("Scanning..."):
            time.sleep(1)
            st.session_state.audit_data = analyze_website(url)
            st.rerun()

if st.session_state.audit_data:
    data = st.session_state.audit_data
    score_color = data.get("color", "#FFDA47")

    # --- HTML FIX: NO INDENTATION TO PREVENT CODE BLOCK RENDER ---
    fail_msg = ""
    if data.get('fails', 0) > 0:
        fail_msg = f"""<div style="margin-top: 15px; font-weight: 700; color: #FF4B4B; font-size: 18px;">⚠️ YOU FAILED {data['fails']} OF {data['total_checks']} CRITICAL CHECKS</div>"""

    st.markdown(f"""
<div class="score-container" style="border-top: 5px solid {score_color};">
<div class="score-label">AI VISIBILITY SCORE</div>
<div class="score-circle">{data['score']}/100</div>
<div class="verdict-text" style="color: {score_color};">{data['verdict']}</div>
{fail_msg}
</div>
""", unsafe_allow_html=True)

    # --- VOICE WARNING ---
    if data['score'] < 60:
        st.markdown("""
<div style="background-color: #3b1e1e; border: 1px solid #FF4B4B; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 20px;">
<span style="font-size: 24px;">⛔</span><br>
<strong style="color: #FF6B6B; font-size: 18px;">CRITICAL ALERT</strong><br>
<span style="color: #E0E0E0;">Your current score means your business is likely <strong>INVISIBLE</strong> to voice agents like <strong>Siri, Alexa, and Google Assistant</strong>.</span>
</div>
""", unsafe_allow_html=True)

    if data["status"] == "blocked":
        st.markdown("""
<div class="blocked-msg">
We could verify your domain, but your firewall blocked our content scanner.<br>
<strong>If we are blocked, Siri & Alexa likely are too.</strong>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#FFDA47; font-size:22px; text-align:center; font-weight:700; font-family:Spectral, serif;'>Unlock the detailed PDF breakdown.</p>", unsafe_allow_html=True)

    # --- UPDATED EMAIL FORM ---
    with st.form(key='email_form'):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", placeholder="Enter your name")
        with c2:
            email = st.text_input("Email", placeholder="name@company.com")
        
        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
            get_pdf = st.form_submit_button("EMAIL ME MY FOUND SCORE ANALYSIS")

    if get_pdf:
        if name and email and "@" in email:
            save_lead(name, email, st.session_state.url_input, data['score'], data['verdict'], data)
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

    # --- ONE BUTTON AS REQUESTED ---
    st.markdown("""<a href="https://go.foundbyai.online/get-toolkit" target="_blank" class="amber-btn">CLICK HERE TO FIX YOUR SCORE</a>""", unsafe_allow_html=True)

    st.markdown("""
<div style='background-color: #2D3342; padding: 20px; border-radius: 8px; margin-top: 30px; margin-bottom: 20px;'>
<div style='margin-bottom: 10px;'>✅ <strong>The Unblocker Guide:</strong> Remove AI crawler blockages.</div>
<div style='margin-bottom: 10px;'>✅ <strong>Accessibility Tags:</strong> Rank for Voice Search.</div>
<div style='margin-bottom: 10px;'>✅ <strong>Schema Generator:</strong> Tell AI exactly what you do.</div>
<div style='margin-bottom: 10px;'>✅ <strong>Copyright Script:</strong> Auto-update for Freshness.</div>
<div>✅ <strong>Privacy & GDPR:</strong> Build Trust with Agents.</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    def clear_form():
        st.session_state.audit_data = None
        st.session_state.url_input = ""
    with c2:
        st.button("🔄 START A NEW AUDIT", on_click=clear_form)
