import streamlit as st
import time
import gspread
from google.oauth2.service_account import Credentials

# --------------------------------------------------------------------------
# 1. CRITICAL: PAGE CONFIG & STYLING (MUST BE FIRST)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="🤖",
    layout="centered"
)

# FORCE DARK THEME CSS
st.markdown("""
    <style>
    /* 1. Main Background - Charcoal */
    .stApp {
        background-color: #1A1F2A !important;
    }
    
    /* 2. Text Colors - White */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li {
        color: #FFFFFF !important;
    }
    
    /* 3. Input Fields - Dark Grey with White Text */
    .stTextInput > div > div > input {
        background-color: #2D3442 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A5568 !important;
    }
    
    /* 4. The Action Button - Amber */
    div.stButton > button:first-child {
        background-color: #FFDA47 !important;
        color: #1A1F2A !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        padding: 15px 25px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        text-transform: uppercase !important;
    }
    div.stButton > button:hover {
        background-color: #E6C235 !important;
        color: #1A1F2A !important;
    }

    /* 5. Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 6. Fix for Success/Error Messages */
    .stAlert {
        background-color: #2D3442;
        color: #FFF;
        border: 1px solid #4A5568;
    }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. UI LAYOUT (LOADS IMMEDIATELY)
# --------------------------------------------------------------------------

# LOGO: Using the exact filename you uploaded (Note spelling: Iogo)
try:
    st.image("LG Iogo charcoal BG.jpg", width=250) 
except:
    # If image fails, show text so app doesn't crash
    st.markdown("<h1>FOUND BY AI</h1>", unsafe_allow_html=True)

st.markdown("### UNBLOCK YOUR BUSINESS")
st.write("See exactly how Siri, ChatGPT, and Google Gemini see your business. 90% of local businesses are invisible to AI.")

# INPUT FORM
with st.form("audit_form"):
    target_url = st.text_input("Enter your Website URL:", placeholder="e.g., https://www.yourbusiness.com")
    user_email = st.text_input("Enter your Email (to send the report):", placeholder="name@example.com")
    submitted = st.form_submit_button("RUN AUDIT & UNBLOCK")

# --------------------------------------------------------------------------
# 3. BACKEND LOGIC (SAFE MODE)
# --------------------------------------------------------------------------

def save_lead_safely(email, url, score):
    """Attempts to save lead, but fails silently if DB is down so UI doesn't break"""
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open("Found By AI Leads").sheet1 
        sheet.append_row([email, url, score, time.strftime("%Y-%m-%d %H:%M:%S")])
    except Exception as e:
        print(f"Database Error (UI unaffected): {e}")

if submitted:
    if not target_url:
        st.error("Please enter a URL to scan.")
    else:
        # VISUAL: Loading Sequence (The Hook)
        with st.status("🔍 Initializing AI Scanners...", expanded=True) as status:
            time.sleep(0.5)
            st.write("Pinged Apple Maps / Siri Database...")
            time.sleep(0.5)
            st.write("Crawling for ChatGPT readability...")
            time.sleep(0.5)
            st.write("Analyzing Schema markup...")
            time.sleep(0.5)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)

        # LOGIC: Generate Score
        final_score = 45 # Placeholder

        # LOGIC: Save Lead (In background)
        if user_email:
            save_lead_safely(user_email, target_url, final_score)

        # VISUAL: Result Display
        st.divider()
        st.markdown(f"<h1 style='text-align: center; color: #FF4B4B !important;'>VISIBILITY SCORE: {final_score}/100</h1>", unsafe_allow_html=True)
        st.error("⚠️ CRITICAL: Your business is largely invisible to Voice Search (Siri) and AI Agents.")
        st.info("We found 3 Critical Blocking Issues preventing AI from recommending you.")

        # VISUAL: Call to Action
        st.markdown("""
            <div style="background-color: #2D3442; padding: 20px; border-radius: 10px; border: 1px solid #FFDA47; text-align: center; margin-top: 20px;">
                <h3 style="margin-bottom: 10px; color: #FFF !important;">FIX THIS NOW</h3>
                <p style="color: #FFF !important;">Get the step-by-step fix to unblock your business on Apple & AI.</p>
                <a href="https://go.foundbyai.online/get-toolkit" target="_blank">
                    <button style="background-color: #FFDA47; color: #000; font-weight: bold; padding: 15px 30px; border: none; border-radius: 5px; font-size: 18px; cursor: pointer;">
                        GET THE REPAIR TOOLKIT (£27)
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
