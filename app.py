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

# --- 2. LIGHTWEIGHT CSV GENERATOR (Zero Dependencies) ---
def convert_to_csv(data_list):
    """
    Converts a list of dictionaries to a downloadable CSV string
    without using Pandas.
    """
    if not data_list:
        return ""
    
    output = io.StringIO()
    # Extract headers dynamically from the first dictionary
    headers = data_list[0].keys()
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data_list)
    
    # Return as bytes for the download button
    return output.getvalue().encode('utf-8')

# --- 3. HELPER: ROBOTS.TXT ANALYZER ---
def check_robots(domain):
    """
    Checks if the domain blocks AI bots via robots.txt.
    """
    try:
        robots_url = f"{domain.rstrip('/')}/robots.txt"
        # Use a generic user agent to fetch the file
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AI-Audit-Bot/1.0)'}
        response = requests.get(robots_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for global block
            if "disallow: /" in content and "user-agent: *" in content:
                return "Blocked", "Global 'Disallow' found in robots.txt."
            
            # Check for specific AI blocks (GPTBot, CCBot, Google-Extended)
            if "gptbot" in content and "disallow" in content:
                return "AI Blocked", "GPTBot is specifically blocked."
            
            return "Passed", "Robots.txt found and AI bots appear allowed."
        else:
            return "Warning", "No robots.txt found (or 404 error)."
            
    except Exception as e:
        return "Error", f"Could not connect to robots.txt: {str(e)}"

# --- 4. CORE AUDIT LOGIC (The Brain) ---
def run_audit(url):
    """
    Scrapes the target URL and runs 6 specific visibility checks.
    Returns a Python list of dictionaries.
    """
    results = []
    
    # User-Agent masquerading as Googlebot to see what Google sees
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    
    # 1. URL Normalization
    if not url.startswith("http"):
        url = "https://" + url
    
    parsed_uri = urlparse(url)
    domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    try:
        # --- A. FETCH THE PAGE ---
        # Using st.toast for a subtle UI notification instead of a blocking spinner text
        st.toast(f"Connecting to {parsed_uri.netloc}...", icon="📡")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # If the site is down or blocks the request
        if response.status_code != 200:
            results.append({
                "Check": "Website Connectivity", 
                "Status": "Critical Fail", 
                "Details": f"Server returned status code {response.status_code}"
            })
            return results 
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- B. EXECUTE CHECKS ---

        # CHECK 1: Robots.txt
        r_status, r_details = check_robots(domain_base)
        results.append({
            "Check": "Robots.txt / AI Access",
            "Status": r_status,
            "Details": r_details
        })

        # CHECK 2: Page Title (Context for AI)
        title = soup.title.string.strip() if soup.title else None
        if title and len(title) > 10:
            results.append({
                "Check": "Page Title (Context)",
                "Status": "Passed",
                "Details": f"Found: '{title[:30]}...'"
            })
        else:
            results.append({
                "Check": "Page Title (Context)",
                "Status": "Failed",
                "Details": "Title tag is missing or too short for AI context."
            })

        # CHECK 3: Meta Description (Summarization)
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'].strip() if desc_tag else None
        
        if desc and len(desc) > 50:
            results.append({
                "Check": "Meta Description",
                "Status": "Passed",
                "Details": "Good description found for AI summarization."
            })
        else:
            results.append({
                "Check": "Meta Description",
                "Status": "Warning",
                "Details": "Description missing or too short."
            })

        # CHECK 4: Schema Markup (Structured Data for Siri/Google SGE)
        # We look for JSON-LD scripts
        schema = soup.find('script', attrs={'type': 'application/ld+json'})
        if schema:
            results.append({
                "Check": "Schema Markup",
                "Status": "Passed",
                "Details": "JSON-LD Schema detected (Excellent for Knowledge Graph)."
            })
        else:
            results.append({
                "Check": "Schema Markup",
                "Status": "Failed",
                "Details": "No Structured Data found. Difficult for Siri to parse."
            })

        # CHECK 5: Apple Touch Icon (Visual Search & Bookmarks)
        apple_icon = soup.find('link', rel='apple-touch-icon')
        if apple_icon:
            results.append({
                "Check": "Apple/Mobile Icon",
                "Status": "Passed",
                "Details": "Apple Touch Icon detected."
            })
        else:
            results.append({
                "Check": "Apple/Mobile Icon",
                "Status": "Warning",
                "Details": "Missing specific icon for Apple devices."
            })

        # CHECK 6: Content Density (Can the LLM read enough?)
        # Remove scripts and styles to count actual visible text
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        
        text_content = soup.get_text()
        # Simple word count
        word_count = len(text_content.split())
        
        if word_count > 300:
             results.append({
                 "Check": "Content Density",
                 "Status": "Passed",
                 "Details": f"~{word_count} words found. Sufficient for LLM training."
             })
        elif word_count > 100:
             results.append({
                 "Check": "Content Density",
                 "Status": "Warning",
                 "Details": f"Only ~{word_count} words. A bit thin for AI indexing."
             })
        else:
             results.append({
                 "Check": "Content Density",
                 "Status": "Failed",
                 "Details": "Very little text content found. Is this a JS-heavy site?"
             })

    except requests.exceptions.Timeout:
        results.append({"Check": "Connection", "Status": "Error", "Details": "The request timed out."})
    except Exception as e:
        results.append({"Check": "Critical Error", "Status": "Error", "Details": str(e)})

    return results

# --- 5. MAIN USER INTERFACE ---
def main():
    st.title("AI Visibility Audit 🤖")
    st.markdown("### Will Siri, ChatGPT, and Google SGE find your business?")
    st.markdown("Enter your URL below to check your technical visibility score.")

    # Input Area
    url = st.text_input("Website URL", placeholder="example.com")
    
    # Go Button
    if st.button("Run Audit", type="primary"):
        if not url:
            st.warning("⚠️ Please enter a URL first.")
        else:
            # Spinner while the logic runs
            with st.spinner("Analyzing Robots.txt, Schema, and Metadata..."):
                
                # 1. Run the Logic
                audit_data = run_audit(url)
                
                # 2. Calculate Score (Dynamic)
                pass_count = sum(1 for x in audit_data if x['Status'] == 'Passed')
                total_checks = len(audit_data)
                if total_checks > 0:
                    final_score = int((pass_count / total_checks) * 100)
                else:
                    final_score = 0
                
                # 3. Display Score prominently
                col_score, col_msg = st.columns([1, 2])
                with col_score:
                    st.metric(label="AI Visibility Score", value=f"{final_score}/100")
                with col_msg:
                    if final_score >= 80:
                        st.success("Excellent! Your site is highly visible to AI agents.")
                    elif final_score >= 50:
                        st.warning("Average. You are missing key data structures.")
                    else:
                        st.error("Poor. AI bots will struggle to understand your business.")

                # 4. Display Data Table (Using Streamlit's native list handling)
                st.subheader("Detailed Breakdown")
                st.dataframe(
                    audit_data, 
                    use_container_width=True,
                    column_config={
                        "Status": st.column_config.TextColumn(
                            "Status",
                            help="Pass/Fail status",
                            validate="^Passed|Failed|Warning|Error$"
                        )
                    }
                )
                
                # 5. Download Button (CSV)
                csv_bytes = convert_to_csv(audit_data)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                
                st.download_button(
                    label="📥 Download Full Report",
                    data=csv_bytes,
                    file_name=f"ai_audit_report_{timestamp}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
