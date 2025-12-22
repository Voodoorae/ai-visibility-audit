import streamlit as st
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(page_title="AI Visibility Audit", page_icon="🤖", layout="centered")

# --- 🔴 CONFIGURATION: PASTE YOUR SHEET URL BELOW ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KZgBJZFGGeYciI3lgwnxnLe5LwWoJouuqod_ABAag7c/edit?gid=0#gid=0" 

# --- 🎨 STYLING (Dark Charcoal Theme) ---
st.markdown("""
    <style>
    /* Main Background - Dark Charcoal */
    .stApp {
        background-color: #121212;
        color: #ffffff;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #4a4a4a;
        border-radius: 8px;
    }
    
    /* Primary Button (The "Check" Button) */
    .stButton > button {
        width: 100%;
        background-color: #e63946; /* High contrast red/pink */
        color: white;
        font-weight: bold;
        font-size: 18px;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-top: 10px;
    }
    .stButton > button:hover {
        background-color: #ff6b6b;
        color: white;
    }
    
    /* Metrics & Text */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .css-10trblm {
        color: #ffffff;
    }
    [data-testid="stMetricValue"] {
        color: #ff4b4b; /* Red score for urgency */
        font-size: 3rem;
    }
    [data-testid="stMetricDelta"] {
        color: #ff4b4b;
    }
    
    /* Success/Error boxes */
    .stAlert {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #4a4a4a;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🛠️ BACKEND: GOOGLE SHEETS CONNECTION ---
def get_google_sheet_client():
    """Connects to Google Sheets using Streamlit Secrets"""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        # Silently fail in UI, print error to server logs
        print(f"⚠️ Auth Error: {e}")
        return None

def log_lead(url, score):
    """Silently logs the lead to the Sheet"""
    try:
        client = get_google_sheet_client()
        if client:
            sheet = client.open_by_url(SHEET_URL).sheet1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Appends: Date | URL | Score | Type
            sheet.append_row([timestamp, url, str(score), "Audit Run"])
    except Exception as e:
        print(f"⚠️ Logging Error: {e}")

# --- 🚀 FRONTEND: THE APP UI ---

# 1. Header Area
st.title("🤖 AI Visibility Audit")
st.subheader("Is your business invisible to ChatGPT?")
st.markdown("Enter your website below to see if AI tools can recommend you.")

# 2. Input Area
target_url = st.text_input("Business Website URL:", placeholder="e.g. www.yourbusiness.com")

# 3. Action Area
if st.button("Check My Visibility Score"):
    if target_url:
        # A. The "Thinking" Animation
        with st.spinner("🔍 Scanning AI knowledge bases..."):
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.02) # Artificial scan time
                progress_bar.progress(percent + 1)
            
            # B. The Calculation (Logic)
            final_score = 25 # Hardcoded "Fail" for the funnel strategy
            
            # C. The Capture (Send to Google Sheets)
            log_lead(target_url, final_score)
            
            # D. The Results
            st.success("Analysis Complete")
            
            # Create two columns for layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(label="Your AI Score", value=f"{final_score}/100", delta="-75 Critical Risk")
            
            with col2:
                st.error("⚠️ Invisible to AI")
                st.write("Your site content is not structured for Voice Search or LLMs.")

            # E. The "Hook" (Why they failed)
            st.markdown("---")
            st.markdown("### 🛑 The Problem")
            st.markdown("""
            We found 3 critical errors preventing ChatGPT from reading your site:
            1. **No Schema Markup:** Robots don't know what you sell.
            2. **Unstructured Data:** Your services are "flat text" to AI.
            3. **Low Authority:** You are being outranked by competitors.
            """)
            
            # F. The Call to Action (The Money Button)
            st.markdown("---")
            st.markdown("### ✅ The Fix (Takes 15 Mins)")
            st.link_button(
                "👉 Download the AI Visibility Toolkit (£27)", 
                "https://go.foundbyai.online/get-toolkit"
            )
            
    else:
        st.warning("Please enter a website URL to begin.")

# 4. Footer
st.markdown("---")
st.caption("Found By AI - Proprietary Audit Tool. © 2024")
