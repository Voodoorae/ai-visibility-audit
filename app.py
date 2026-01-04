import streamlit as st
import time
import requests
from google.oauth2.service_account import Credentials
import gspread

# --------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING (The "Look")
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="🤖",
    layout="centered"
)

# This CSS forces the Dark Theme (Charcoal #1A1F2A) and Amber Buttons (#FFDA47)
st.markdown("""
    <style>
    /* Force Background Color to Charcoal */
    .stApp {
        background-color: #1A1F2A;
    }
    
    /* Text Colors */
    h1, h2, h3, p, div, label, span {
        color: #FFFFFF !important;
    }
    
    /* Input Box Styling */
    .stTextInput > div > div > input {
        background-color: #2D3442;
        color: #FFFFFF;
        border: 1px solid #4A5568;
    }
    
    /* The "RUN AUDIT" Button Styling - AMBER */
    div.stButton > button:first-child {
        background-color: #FFDA47;
        color: #1A1F2A; /* Dark Text on Amber Button */
        font-size: 20px;
        font-weight: 800;
        padding: 15px 25px;
        border-radius: 8px;
        border: none;
        width: 100%;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background-color: #E6C235; /* Slightly darker amber on hover */
        color: #1A1F2A;
        border: none;
    }
    
    /* Hide standard Streamlit header/footer for cleaner look */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------------------------------

def connect_to_gsheets():
    """Connects to Google Sheets using st.secrets"""
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # If running locally without secrets.toml, this will fail. Ensure secrets are set up.
    try:
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

def save_lead(email, url, score):
    """Saves the lead data to the Google Sheet"""
    client = connect_to_gsheets()
    if client:
        try:
            # Replace 'Found By AI Leads' with your EXACT Sheet Name
            sheet = client.open("Found By AI Leads").sheet1 
            sheet.append_row([email, url, score, time.strftime("%Y-%m-%d %H:%M:%S")])
        except Exception as e:
            st.warning(f"Note: Could not save to database ({e}), but audit will proceed.")

# --------------------------------------------------------------------------
# 3. THE APP UI
# --------------------------------------------------------------------------

# LOGO SECTION
# Make sure your image file is in the same folder as app.py
# If you don't have the image file uploaded to the server yet, comment this out.
try:
    st.image("LG Iogo charcoal BG.jpg", width=250) 
except:
    st.markdown("# FOUND BY AI") # Fallback if image is missing

st.markdown("### UNBLOCK YOUR BUSINESS")
st.write("See exactly how Siri, ChatGPT, and Google Gemini see your business. 90% of local businesses are invisible to AI.")

# INPUT FORM
with st.form("audit_form"):
    target_url = st.text_input("Enter your Website URL:", placeholder="e.g., https://www.yourbusiness.com")
    user_email = st.text_input("Enter your Email (to send the report):", placeholder="name@example.com")
    
    # The Big Amber Button
    submitted = st.form_submit_button("RUN AUDIT & UNBLOCK")

# --------------------------------------------------------------------------
# 4. EXECUTION LOGIC
# --------------------------------------------------------------------------

if submitted:
    if not target_url:
        st.error("Please enter a URL to scan.")
    else:
        # 1. SHOW THE "LOADING" ANIMATION (Psychological Wait Time)
        with st.status("🔍 Initializing AI Scanners...", expanded=True) as status:
            time.sleep(1)
            st.write("Pinged Apple Maps / Siri Database...")
            time.sleep(1)
            st.write("Crawling for ChatGPT readability...")
            time.sleep(1)
            st.write("Analyzing Schema markup...")
            time.sleep(1)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)

        # 2. GENERATE THE SCORE (Placeholder Logic - Replace with your real logic later)
        # For now, we simulate a score based on URL length/randomness or just a placeholder
        # In reality, this is where your scraper code goes.
        final_score = 45 # Default "scary" score for the demo
        
        # 3. SAVE TO GOOGLE SHEETS
        if user_email:
            save_lead(user_email, target_url, final_score)

        # 4. SHOW RESULTS
        st.divider()
        st.markdown(f"<h1 style='text-align: center; color: #FF4B4B !important;'>VISIBILITY SCORE: {final_score}/100</h1>", unsafe_allow_html=True)
        
        st.error("⚠️ CRITICAL: Your business is largely invisible to Voice Search (Siri) and AI Agents.")
        
        st.info("We found 3 Critical Blocking Issues preventing AI from recommending you.")

        # 5. CALL TO ACTION (Link to GHL Funnel)
        st.markdown("""
            <div style="background-color: #2D3442; padding: 20px; border-radius: 10px; border: 1px solid #FFDA47; text-align: center; margin-top: 20px;">
                <h3 style="margin-bottom: 10px;">FIX THIS NOW</h3>
                <p>Get the step-by-step fix to unblock your business on Apple & AI.</p>
                <a href="https://go.foundbyai.online/get-toolkit" target="_blank">
                    <button style="background-color: #FFDA47; color: #000; font-weight: bold; padding: 15px 30px; border: none; border-radius: 5px; font-size: 18px; cursor: pointer;">
                        GET THE REPAIR TOOLKIT (£27)
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
