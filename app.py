import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import csv
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="AI Visibility Audit",
    page_icon="🤖",
    layout="centered"
)

# --- 2. GOOGLE SHEETS CONNECTION (The Logger) ---
def connect_to_sheet():
    """
    Connects to Google Sheets using Streamlit Secrets.
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        # Load credentials from Streamlit secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open the Sheet (Make sure your sheet is named EXACTLY this)
        sheet = client.open("FoundByAI_Leads").sheet1 
        return sheet
    except Exception as e:
        return None

def log_audit_to_sheet(sheet, url, score, audit_data):
    """
    Logs the scan details to a row in Google Sheets.
    Row Format: [Date, URL, Score, Robots, Schema, Meta, Apple, Content]
    """
    if not sheet:
        return

    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract specific statuses for the columns
        robots_status = next((item['Status'] for item in audit_data if "Robots" in item['Check']), "N/A")
        schema_status = next((item['Status'] for item in audit_data if "Schema" in item['Check']), "N/A")
        meta_status = next((item['Status'] for item in audit_data if "Description" in item['Check']), "N/A")
        
        # Create the row
        row = [timestamp, url, score, robots_status, schema_status, meta_status]
        
        # Append to sheet
        sheet.append_row(row)
    except:
        pass # Fail silently so the user never knows if logging fails

# --- 3. CSV EXPORT FUNCTION (Zero-Dependency) ---
def convert_to_csv(data_list):
    if not data_list:
        return ""
    output = io.StringIO()
    headers = data_list[0].keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data_list)
    return output.getvalue().encode('utf-8')

# --- 4. HELPER: ROBOTS.TXT CHECKER ---
def check_robots(domain):
    try:
        robots_url = f"{domain.rstrip('/')}/robots.txt"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AI-Audit-Bot/1.0)'}
        response = requests.get(robots_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            content = response.text.lower()
            if "disallow: /" in content and "user-agent: *" in content:
                return "Blocked", "Global 'Disallow' found in robots.txt."
            if "gptbot" in content and "disallow" in content:
                return "AI Blocked", "GPTBot (ChatGPT) is specifically blocked."
            return "Passed", "Robots.txt found. AI bots are allowed."
        else:
            return "Warning", "No robots.txt found."
    except Exception as e:
        return "Error", f"Could not fetch robots.txt: {str(e)}"

# --- 5. CORE AUDIT ENGINE ---
def run_audit(url):
    results = []
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        parsed_uri = urlparse(url)
        domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    except:
        results.append({"Check": "URL Format", "Status": "Error", "Details": "Invalid URL."})
        return results

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    try:
        st.toast(f"Scanning {parsed_uri.netloc}...", icon="📡")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            results.append({"Check": "Server Status", "Status": "Critical Fail", "Details": f"Error {response.status_code}"})
            return results 
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- CHECKS ---
        r_status, r_details = check_robots(domain_base)
        results.append({"Check": "Robots.txt Access", "Status": r_status, "Details": r_details})

        title = soup.title.string.strip() if soup.title else None
        if title and len(title) > 5:
            results.append({"Check": "Page Title", "Status": "Passed", "Details": f"Found: '{title[:30]}...'"})
        else:
            results.append({"Check": "Page Title", "Status": "Failed", "Details": "Title missing."})

        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else None
        if desc and len(desc) > 50:
            results.append({"Check": "Meta Description", "Status": "Passed", "Details": "Description found."})
        else:
            results.append({"Check": "Meta Description", "Status": "Warning", "Details": "Description missing/short."})

        schema = soup.find('script', attrs={'type': 'application/ld+json'})
        if schema:
            results.append({"Check": "Schema Markup", "Status": "Passed", "Details": "JSON-LD Schema found."})
        else:
            results.append({"Check": "Schema Markup", "Status": "Failed", "Details": "No Structured Data found."})

        apple_icon = soup.find('link', rel='apple-touch-icon')
        if apple_icon:
            results.append({"Check": "Apple Icon", "Status": "Passed", "Details": "Apple Icon found."})
        else:
            results.append({"Check": "Apple Icon", "Status": "Warning", "Details": "Missing Apple icon."})

        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        text_content = soup.get_text()
        words = len(text_content.split())
        
        if words > 300:
             results.append({"Check": "Content Density", "Status": "Passed", "Details": f"~{words} words found."})
        else:
             results.append({"Check": "Content Density", "Status": "Warning", "Details": f"Thin content (~{words} words)."})

    except Exception as e:
        results.append({"Check": "Critical Error", "Status": "Error", "Details": str(e)})

    return results

# --- 6. MAIN UI ---
def main():
    st.title("AI Visibility Audit 🤖")
    st.markdown("### Will Siri, ChatGPT, and Google SGE find your business?")

    url_input = st.text_input("Website URL", placeholder="example.com")
    
    if st.button("Run Audit", type="primary"):
        if not url_input:
            st.warning("⚠️ Please enter a URL.")
        else:
            with st.spinner("Analyzing site structure..."):
                
                # 1. Run Audit
                audit_data = run_audit(url_input)
                
                # 2. Calculate Score
                passed = sum(1 for x in audit_data if x['Status'] == 'Passed')
                total = len(audit_data)
                score = int((passed / total) * 100) if total > 0 else 0
                
                # 3. SILENT LOGGING (Google Sheets)
                sheet = connect_to_sheet()
                if sheet:
                    log_audit_to_sheet(sheet, url_input, score, audit_data)
                
                # 4. Display Results
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("AI Visibility Score", f"{score}/100")
                with col2:
                    if score >= 80:
                        st.success("Your site is optimized for AI agents!")
                    elif score >= 50:
                        st.warning("Average. You are missing key data structures.")
                    else:
                        st.error("Poor. AI bots cannot read your site effectively.")

                st.subheader("Audit Details")
                st.dataframe(audit_data, use_container_width=True, hide_index=True)
                
                csv_file = convert_to_csv(audit_data)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                
                st.download_button(
                    label="📥 Download Report (CSV)",
                    data=csv_file,
                    file_name=f"ai_audit_{timestamp}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
