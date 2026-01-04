import streamlit as st
import time

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
    
    /* Text Colors - Force White */
    h1, h2, h3, p, div, label, span, li {
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
    
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. THE APP UI
# --------------------------------------------------------------------------

# LOGO: Trying to load your image. If it fails, it prints text instead of crashing.
try:
    st.image("LG Iogo charcoal BG.jpg", width=250) 
except:
    st.markdown("<h1>FOUND BY AI</h1>", unsafe_allow_html=True)

st.markdown("### UNBLOCK YOUR BUSINESS")
st.write("See exactly how Siri, ChatGPT, and Google Gemini see your business. 90% of local businesses are invisible to AI.")

# INPUT FORM
with st.form("audit_form"):
    target_url = st.text_input("Enter your Website URL:", placeholder="e.g., https://www.yourbusiness.com")
    user_email = st.text_input("Enter your Email (to send the report):", placeholder="name@example.com")
    
    # The Big Amber Button
    submitted = st.form_submit_button("RUN AUDIT & UNBLOCK")

# --------------------------------------------------------------------------
# 3. FAKE EXECUTION (To test UI only)
# --------------------------------------------------------------------------

if submitted:
    if not target_url:
        st.error("Please enter a URL to scan.")
    else:
        # Loading Animation
        with st.status("🔍 Initializing AI Scanners...", expanded=True) as status:
            time.sleep(0.5)
            st.write("Pinged Apple Maps / Siri Database...")
            time.sleep(0.5)
            st.write("Crawling for ChatGPT readability...")
            time.sleep(0.5)
            status.update(label="✅ Scan Complete!", state="complete", expanded=False)

        # Mock Score
        final_score = 45 

        # Results
        st.divider()
        st.markdown(f"<h1 style='text-align: center; color: #FF4B4B !important;'>VISIBILITY SCORE: {final_score}/100</h1>", unsafe_allow_html=True)
        st.error("⚠️ CRITICAL: Your business is largely invisible to Voice Search (Siri) and AI Agents.")
        st.info("We found 3 Critical Blocking Issues preventing AI from recommending you.")

        # CTA Button
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
