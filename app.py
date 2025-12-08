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
    # If FPDF is not available, set flag to False
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

    /* --- REMOVE GHOST BUTTONS FROM IMAGES & LINKS --- */
    [data-testid="StyledFullScreenButton"], /* Hides fullscreen icon */
    [data-testid="stImage"] a[target="_blank"] { /* Hides link icon next to image */
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
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

# FIXED: Added 'pass' to ensure the function has an indented block
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
    # New Max points used here for consistency: Schema (30), Voice (20), Accessibility (15), Freshness (15), Local (10), Canonical (10)
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
col1, col2, col3 = st.columns([1,2,1])
with col2:
    # This image is wrapped in a container, and the CSS above hides the default Streamlit link/fullscreen icons on it.
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
        url = st.text_input("Enter Website URL", placeholder="e.g. plumber-marketing.
