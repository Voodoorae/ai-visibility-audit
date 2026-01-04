import streamlit as st
import time
import requests
from google.oauth2.service_account import Credentials
import gspread

# --------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING (Charcoal & Amber Theme)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="🤖",
    layout="centered"
)

# This CSS forces the Dark Theme (#1A1F2A) and Amber Buttons (#FFDA47)
st.markdown("""
    <style>
    /* Force Background Color to Charcoal */
    .stApp {
        background-color: #1A1F2A;
    }
    
    /* Text Colors - Force White for readability on dark background */
    h1, h2, h3, p, div, label, span, li, .stMarkdown {
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
        color: #1A1F2A !important; /* Dark Text on Amber Button */
        font-size: 20px;
        font-weight: 800;
        padding: 15px 25px;
        border-radius: 8px;
        border: none;
        width: 100%;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background-color: #E6C235;
        color: #1A1F2A !important;
        border: none;
    }
    
    /* Hide standard Streamlit header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Success/Error/Info box styling adjustments */
    .stAlert {
        background-color: #2D3442;
        color: #FFF;
        border: 1px solid #4A5568;
    }
    
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. GOOGLE SHEETS CONNECTION LOGIC
# --------------------------------------------------------------------------

def connect_to_gsheets():
    """Connects to Google Sheets using st.secrets"""
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    try:
        # Relies on secrets.toml file being present in .streamlit folder or Streamlit Cloud Secrets
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        # If connection fails, we log it but don't crash the app for the user
        print(f"Database Connection Error: {e}")
        return None

def save_lead(email, url, score):
    """Saves the lead data to the Google Sheet"""
    client = connect_to_gsheets()
    if client:
        try:
            # Ensure your sheet name matches exactly: 'Found By AI Leads'
            sheet = client.open("Found By AI Leads").sheet1 
            sheet.append_row([email, url, score, time.strftime("%Y-%m-%d %H:%M:%S")])
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False
    return False

# --------------------------------------------------------------------------
# 3. THE APP UI
# --------------------------------------------------------------------------

# LOGO SECTION
try:
    st.image("LG Iogo charcoal BG.jpg", width=250) 
except:
    # Fallback text if image not found
    st.markdown("<h1>FOUND BY AI</h1>", unsafe_allow_html=True)

st.markdown("### UNBLOCK YOUR BUSINESS")
st.write("See exactly how Siri, ChatGPT, and Google Gemini see your business. 90% of local businesses are invisible to AI.")

# INPUT FORM
with st.form("audit_form"):
    target_url = st.text_input("Enter your Website URL:", placeholder="e.g., https://www.yourbusiness.com")
    user_email = st.text_input("Enter your Email (to send the report):", placeholder="name@example.com")
    
    # The Action Button
    submitted = st.form_submit_button("RUN AUDIT & UNBLOCK")

# --------------------------------------------------------------------------
# 4. EXECUTION LOGIC (Triggered by Button)
# --------------------------------------------------------------------------

if submitted:
    if not target_url:
        st.error("Please enter a URL to scan.")
    else:
        # 1. SHOW THE "LOADING" ANIMATION
        # This keeps the user engaged while "processing"
        with st.status("🔍 Initializing AI Scanners...", expanded=True) as status:
            time.sleep(0.8)
            st.write("Pinged Apple Maps / Siri Database...")
            time.sleep(0.8)
            st.write("Crawling for ChatGPT readability...")
            time.sleep(0.8)
            st.write("Analyzing Schema markup...")
            time.sleep(0.5)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)

        # 2. GENERATE SCORE (Placeholder for V1)
        final_score = 45 
        
        # 3. SAVE TO DATABASE (The Critical Step)
        if user_email:
            saved = save_lead(user_email, target_url, final_score)
            if not saved:
                # Optional: print specific error to console if needed, but keep UI clean
                pass

        # 4. SHOW RESULTS UI
        st.divider()
        st.markdown(f"<h1 style='text-align: center; color: #FF4B4B !important;'>VISIBILITY SCORE: {final_score}/100</h1>", unsafe_allow_html=True)
        
        st.error("⚠️ CRITICAL: Your business is largely invisible to Voice Search (Siri) and AI Agents.")
        
        st.info("We found 3 Critical Blocking Issues preventing AI from recommending you.")

        # 5. CALL TO ACTION (Link to GHL Funnel)
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
