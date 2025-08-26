import streamlit as st
import fitz
import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, cellFormat, textFormat, set_column_width

# --- ANALYSIS LOGIC ---
# This is the full analysis function from your original code.
def analyze_nda_text(nda_text):
    """Analyzes the NDA text for compliance and generates feedback."""
    feedback = []
    try:
        # Governing State
        ny_patterns = [r"New York", r"N\.Y\.", r"(?<![a-zA-Z])NY(?![a-zA-Z])"]
        de_patterns = [r"Delaware", r"D\.E\.", r"(?<![a-zA-Z])DE(?![a-zA-Z])"]

        has_ny = any(re.search(p, nda_text, re.IGNORECASE) for p in ny_patterns)
        has_de = any(re.search(p, nda_text, re.IGNORECASE) for p in de_patterns)

        if not (has_ny or has_de):
            feedback.append(["Governing State", "Our preferred governing states were not found. Ensure the Agreement is governed in New York State or Delaware.\n\n"])

        # Exclusive Jurisdiction
        exclusive_jurisdiction_patterns = [r"exclusive jurisdiction and venue", r"exclusive jurisdiction"]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in exclusive_jurisdiction_patterns):
            feedback.append(["Exclusive Jurisdiction", "Insert: Exclusive jurisdiction and venue for any action arising under this [Agreement] shall be in the federal and state courts located in [NY/DE], and both parties hereby consent to such jurisdiction and venue for this purpose.\n\n"])

        # Burdensome Requests
        burden_words = {
            r"\bImmediately\b": "'Immediately' is burdensome. Replace with 'promptly'.\n\n",
            r"\bImmediate\b": "'Immediate' is burdensome. Replace with 'prompt'.\n\n",
            r"\bcertify\b": "'Certify' is burdensome. Replace with 'confirm'.\n\n",
            r"\bcertification\b": "'Certification' is burdensome. Replace with 'confirmation'.\n\n",
            r"\bcertified\b": "'Certified' is burdensome. Replace with 'confirmed'.\n\n",
            r"\bindemnity\b|\bindemnification\b": "Indemnities are burdensome. Delete entire clause.\n\n",
            r"\bprove\b": "'Prove' is burdensome. Replace with 'demonstrate upon reasonable evidence'.\n\n",
            r"\bproving\b": "'Proving' is burdensome. Replace with 'demonstrating upon reasonable evidence'.\n\n",
            r"\bbest\b": "'Best' is sometimes burdensome. If appropriate, qualify with 'reasonable best'.\n\n",
            r"\bopinion\b": "'Opinion' is burdensome because it is a legal document. Delete.\n\n",
            r"\bopine\b": "'Opine' is burdensome. Delete.\n\n",
            r"\boccur\b": "'Occur' is burdensome. Replace with 'become known to the receiving party'.\n\n",
            r"\boccurs\b": "'Occurs' is burdensome. Replace with 'becomes known to the receiving party'.\n\n",
            r"\boccurred\b": "'Occurred' is burdensome. Replace with 'became known to the receiving party'.\n\n",
            r"\bNon-Solicitation\b": "Reference to non-solicitation was found. Ensure inclusion of the following qualifiers: (a) senior employees, (b) become known to me as a result of transactions contemplated by this [Agreement], (c) annual cash compensation exceeds US$250,000 per year,  (d) provided, that, (i) general solicitations for employment (including the use of employment agencies not directly targeting the [Seller] or any of the [Sellers] employees) conducted by or on behalf of [Capsule] (ii) an employee contacting [Capsule] on their own initiative (iii) employees who have been terminated by the [Seller], shall not constitute a violation of the foregoing restrictions.\n\n",
            r"\bNon-Solicit\b": "Reference to a non-solicit clause was found. Ensure inclusion of the following qualifiers: (a) senior employees, (b) become known to me as a result of transactions contemplated by this [Agreement], (c) annual cash compensation exceeds US$250,000 per year,  (d) provided, that, (i) general solicitations for employment (including the use of employment agencies not directly targeting the [Seller] or any of the [Sellers] employees) conducted by or on behalf of [Capsule] (ii) an employee contacting [Capsule] on their own initiative (iii) employees who have been terminated by the [Seller], shall not constitute a violation of the foregoing restrictions.\n\n"
        }
        for pattern, recommendation in burden_words.items():
            if re.search(pattern, nda_text, re.IGNORECASE):
                if "indemnity" in pattern:
                    feedback.append(["Burdensome Requests", f"{recommendation} If cannot delete, limit to third-party claims and make mutual.\n\n"])
                else:
                    feedback.append(["Burdensome Requests", recommendation])

        # ... (Include all other checks from your original script here) ...

        # Create a DataFrame for results
        results_df = pd.DataFrame(feedback, columns=["Category", "Recommendation"])
        return results_df
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        return pd.DataFrame()

 # --- NEW: Display Results Directly on the Page ---
    st.subheader("Analysis Results")
    
    if results_df.empty:
        st.success("✅ All Clear! No major issues were found based on the playbook.")
    else:
        st.warning(f"🔍 Found {len(results_df)} items that require your attention.")
        
        # Loop through the DataFrame rows and display each piece of feedback
        for index, row in results_df.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Category']}**")
                st.write(row['Recommendation'])

# --- Main App Interface ---
st.title("📄 NDA Review Automation")
st.write("Upload a Non-Disclosure Agreement (PDF) to automatically check it against our standard playbook.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()

    with st.spinner(f"Analyzing '{uploaded_file.name}'... Please wait."):
        # Extract text
        nda_text = ""
        with fitz.open(stream=bytes_data, filetype="pdf") as doc:
            for page in doc:
                nda_text += page.get_text("text") + "\n"
        
        # Analyze and create the sheet
        results_df = analyze_nda_text(nda_text)
        sheet_url = create_google_sheet(results_df, uploaded_file.name)

    if sheet_url:
        st.success("Analysis Complete!")
        st.markdown(f"### [Click Here to View Your NDA Review]({sheet_url})")
    else:
        st.error("There was a problem generating the review. Please try again.")
