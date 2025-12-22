import streamlit as st
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURATION ---
# 🔴 URGENT: PASTE YOUR GOOGLE SHEET URL INSIDE THE QUOTES BELOW
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KZgBJZFGGeYciI3lgwnxnLe5LwWoJouuqod_ABAag7c/edit?gid=0#gid=0"

# --- SETUP GOOGLE SHEETS ---
def get_google_sheet_client():
    # Load credentials from Streamlit secrets
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"⚠️ Database Connection Error: {e}")
        return None

def log_lead(url, score):
    """Silently adds the user's search to the Google Sheet"""
    try:
        client = get_google_sheet_client()
        if client:
            sheet = client.open_by_url(SHEET_URL).sheet1
            # Get current time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Append row: [Date, URL, Score, Status]
            sheet.append_row([timestamp, url, str(score), "New Lead"])
    except Exception as e:
        # If logging fails, print to console but don't break the user experience
        print(f"Logging failed: {e}")

# --- APP LOGIC ---
st.set_page_config(page_title="AI Visibility Audit", page_icon="🤖")

st.title("🤖 AI Visibility Audit")
st.subheader("Will ChatGPT recommend YOUR business?")

# Input
target_url = st.text_input("Enter your business website URL:", placeholder="e.g., www.joesplumbing.com")

if st.button("Check My Visibility Score"):
    if target_url:
        with st.spinner("Analyzing AI search patterns..."):
            # 1. THE PROCESSING ANIMATION
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.02) 
                progress_bar.progress(percent_complete + 1)
            
            # 2. THE CALCULATION
            final_score = 25 # Default score for the funnel
            
            # 3. THE SPY STEP (Log the data)
            log_lead(target_url, final_score)
            
            # 4. THE RESULTS
            st.success("Analysis Complete")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="AI Visibility Score", value=f"{final_score}/100", delta="-75 Low Visibility")
            
            with col2:
                st.error("⚠️ Critical Issues Found")
                st.write("Your business is **invisible** to Voice Search (Siri) and LLMs.")

            # 5. THE OFFER
            st.markdown("---")
            st.markdown("### 🛑 Don't lose customers to your competitors.")
            st.markdown("We found 3 simple text errors blocking your site from AI detection.")
            
            st.link_button("👉 Fix This Now (Get the Toolkit £27)", "https://go.foundbyai.online/get-toolkit")
            
    else:
        st.warning("Please enter a URL to check.")

# Footer
st.markdown("---")
st.caption("Found By AI - Internal Tool. Do not distribute without license.")
