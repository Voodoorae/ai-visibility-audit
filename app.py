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

# --- GOOGLE SHEETS IMPORTS ---
import gspread
from google.oauth2.service_account import Credentials

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Found By AI - Visibility Audit",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

/* --- 1. WIDE WIDTH (1000px) --- */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1000px; 
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

/* UNIFIED HEADER STYLE */
.input-header {
    text-align: center;
    color: #FFFFFF; /* White */
    font-weight: 600; /* Bold */
    font-family: 'Inter', sans-serif;
    margin-bottom: 12px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.3;
    font-size: 20px;
    width: 100%;
}

/* Mobile Tweaks */
@media (max-width: 600px) {
    .input-header {
        font-size: 18px !important;
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
