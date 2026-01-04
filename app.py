import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import datetime
import csv
import io
from urllib.parse import urlparse

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="AI Visibility Audit",
    page_icon="🤖",
    layout="centered"
)

# --- 2. CSV EXPORT FUNCTION (Zero-Dependency) ---
def convert_to_csv(data_list):
    """
    Converts a list of dictionaries to a CSV string for download.
    Replaces pandas.to_csv to keep the app lean.
    """
    if not data_list:
        return ""
    
    output = io.StringIO()
    # Dynamically get headers from the keys of the first item
    headers = data_list[0].keys()
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data_list)
    
    return output.getvalue().encode('utf-8')

# --- 3. HELPER: ROBOTS.TXT CHECKER ---
def check_robots(domain):
    """
    Checks if the domain's robots.txt blocks AI scrapers.
    """
    try:
        robots_url = f"{domain.rstrip('/')}/robots.txt"
        # Use a polite User-Agent for this specific check
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AI-Audit-Bot/1.0)'}
        response = requests.get(robots_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for total block
            if "disallow: /" in content and "user-agent: *" in content:
                return "Blocked", "Global 'Disallow' found in robots.txt."
            
            # Check for specific AI blocks
            if "gptbot" in content and "disallow" in content:
                return "AI Blocked", "GPTBot (ChatGPT) is specifically blocked."
            
            return "Passed", "Robots.txt found. AI bots are allowed."
        else:
            return "Warning", "No robots.txt found (or file is inaccessible)."
            
    except Exception as e:
        return "Error", f"Could not fetch robots.txt: {str(e)}"

# --- 4. CORE AUDIT ENGINE ---
def run_audit(url):
    """
    The main logic. Scrapes the site and runs all checks.
    Returns a simple list of dictionaries (lightweight data structure).
    """
    results = []
    
    # 1. Normalize URL
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        parsed_uri = urlparse(url)
        domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    except:
        results.append({"Check": "URL Format", "Status": "Error", "Details": "Invalid URL format."})
        return results

    # 2. Fetch the Page
    # We masquerade as Googlebot to see what the search engines see
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    try:
        st.toast(f"Scanning {parsed_uri.netloc}...", icon="📡")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            results.append({
                "Check": "Server Status", 
                "Status": "Critical Fail", 
                "Details": f"Website returned error code: {response.status_code}"
            })
            return results 
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- CHECK A: ROBOTS.TXT ---
        r_status, r_details = check_robots(domain_base)
        results.append({
            "Check": "Robots.txt Access",
            "Status": r_status,
            "Details": r_details
        })

        # --- CHECK B: TITLE TAG (Context) ---
        title = soup.title.string.strip() if soup.title else None
        if title and len(title) > 5:
            results.append({
                "Check": "Page Title",
                "Status": "Passed",
                "Details": f"Found: '{title[:40]}...'"
            })
        else:
            results.append({
                "Check": "Page Title",
                "Status": "Failed",
                "Details": "Title tag is missing or empty. AI cannot identify this page."
            })

        # --- CHECK C: META DESCRIPTION (Summaries) ---
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else None
        
        if desc and len(desc) > 50:
            results.append({
                "Check": "Meta Description",
                "Status": "Passed",
                "Details": "Good description found for AI summaries."
            })
        else:
            results.append({
                "Check": "Meta Description",
                "Status": "Warning",
                "Details": "Description is missing or too short."
            })

        # --- CHECK D: SCHEMA MARKUP (Structured Data) ---
        # This is the #1 signal for "Found by AI"
        schema = soup.find('script', attrs={'type': 'application/ld+json'})
        if schema:
            results.append({
                "Check": "Schema Markup",
                "Status": "Passed",
                "Details": "JSON-LD Schema found. (Crucial for Siri/Google SGE)."
            })
        else:
            results.append({
                "Check": "Schema Markup",
                "Status": "Failed",
                "Details": "No Structured Data found. AI cannot easily parse business info."
            })

        # --- CHECK E: APPLE TOUCH ICON (Visual Search) ---
        apple_icon = soup.find('link', rel='apple-touch-icon')
        if apple_icon:
            results.append({
                "Check": "Apple Icon",
                "Status": "Passed",
                "Details": "Apple Touch Icon detected."
            })
        else:
            results.append({
                "Check": "Apple Icon",
                "Status": "Warning",
                "Details": "Missing icon for Apple devices/bookmarks."
            })

        # --- CHECK F: CONTENT DENSITY (LLM Training Data) ---
        # Remove code blocks to count real words
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.extract()
        
        text_content = soup.get_text()
        words = len(text_content.split())
        
        if words > 300:
             results.append({
                 "Check": "Content Density",
                 "Status": "Passed",
                 "Details": f"~{words} words. Good depth for LLM understanding."
             })
        elif words > 50:
             results.append({
                 "Check": "Content Density",
                 "Status": "Warning",
                 "Details": f"Only ~{words} words. Thin content."
             })
        else:
             results.append({
                 "Check": "Content Density",
                 "Status": "Failed",
                 "Details": "Page appears empty or relies entirely on JavaScript."
             })

    except requests.exceptions.Timeout:
        results.append({"Check": "Connection", "Status": "Error", "Details": "Request timed out."})
    except Exception as e:
        results.append({"Check": "Critical Error", "Status": "Error", "Details": str(e)})

    return results

# --- 5. MAIN UI ---
def main():
    st.title("AI Visibility Audit 🤖")
    st.markdown("### Will Siri, ChatGPT, and Google SGE find your business?")
    st.markdown("Enter a website URL to scan for technical AI compatibility.")

    # Input
    url_input = st.text_input("Website URL", placeholder="example.com")
    
    # Logic
    if st.button("Run Audit", type="primary"):
        if not url_input:
            st.warning("⚠️ Please enter a URL.")
        else:
            with st.spinner("Analyzing site structure..."):
                
                # Run the audit
                audit_data = run_audit(url_input)
                
                # Calculate Score
                passed = sum(1 for x in audit_data if x['Status'] == 'Passed')
                total = len(audit_data)
                score = int((passed / total) * 100) if total > 0 else 0
                
                # Display Score
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

                # Display Data Table
                st.subheader("Audit Details")
                st.dataframe(
                    audit_data, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # CSV Download Logic
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

