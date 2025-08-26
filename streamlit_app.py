import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io

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
            feedback.append(["Governing State", "Our preferred governing states were not found. Ensure the Agreement is governed in New York State or Delaware."])

        # Exclusive Jurisdiction
        exclusive_jurisdiction_patterns = [r"exclusive jurisdiction and venue", r"exclusive jurisdiction"]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in exclusive_jurisdiction_patterns):
            feedback.append(["Exclusive Jurisdiction", "Insert: Exclusive jurisdiction and venue for any action arising under this [Agreement] shall be in the federal and state courts located in [NY/DE], and both parties hereby consent to such jurisdiction and venue for this purpose."])

        # Burdensome Requests
        burden_words = {
            r"\bImmediately\b": "'Immediately' is burdensome. Replace with 'promptly'.",
            r"\bImmediate\b": "'Immediate' is burdensome. Replace with 'prompt'.",
            r"\bcertify\b": "'Certify' is burdensome. Replace with 'confirm'.",
            r"\bcertification\b": "'Certification' is burdensome. Replace with 'confirmation'.",
            r"\bcertified\b": "'Certified' is burdensome. Replace with 'confirmed'.",
            r"\bindemnity\b|\bindemnification\b": "Indemnities are burdensome. Delete entire clause. If cannot delete, limit to third-party claims and make mutual.",
            r"\bprove\b": "'Prove' is burdensome. Replace with 'demonstrate upon reasonable evidence'.",
            r"\bproving\b": "'Proving' is burdensome. Replace with 'demonstrating upon reasonable evidence'.",
            r"\bbest\b": "'Best' is sometimes burdensome. If appropriate, qualify with 'reasonable best'.",
            r"\bopinion\b": "'Opinion' is burdensome because it is a legal document. Delete.",
            r"\bopine\b": "'Opine' is burdensome. Delete.",
            r"\boccur\b": "'Occur' is burdensome. Replace with 'become known to the receiving party'.",
            r"\boccurs\b": "'Occurs' is burdensome. Replace with 'becomes known to the receiving party'.",
            r"\boccurred\b": "'Occurred' is burdensome. Replace with 'became known to the receiving party'.",
            r"\bNon-Solicitation\b|\bNon-Solicit\b": "Reference to non-solicitation was found. Ensure inclusion of the following qualifiers: (a) senior employees, (b) become known to me as a result of transactions contemplated by this [Agreement], (c) annual cash compensation exceeds US$250,000 per year, and (d) specific carve-outs for general solicitations, employees who contact you first, and terminated employees."
        }
        for pattern, recommendation in burden_words.items():
            if re.search(pattern, nda_text, re.IGNORECASE):
                feedback.append(["Burdensome Requests", recommendation])
        
        # Non-disparagement
        non_disparagement_patterns = [r"non-disparagement", r"disparagement", r"non[- ]?disparage"]
        if any(re.search(p, nda_text, re.IGNORECASE) for p in non_disparagement_patterns):
            feedback.append(["Non-disparagement", "Delete the non-disparagement clause."])

        # ... (Add any other checks you had in your original script here) ...

        results_df = pd.DataFrame(feedback, columns=["Category", "Recommendation"])
        # Remove duplicate recommendations within the same category
        results_df = results_df.drop_duplicates()
        return results_df
        
    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        return pd.DataFrame()


# --- STREAMLIT APP INTERFACE ---
st.set_page_config(page_title="NDA Reviewer", page_icon="📄")

st.title("📄 NDA Review Automation")
st.write("Upload a Non-Disclosure Agreement (PDF) to automatically check it against our standard playbook.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Read the uploaded file's content
    bytes_data = uploaded_file.getvalue()
    
    with st.spinner(f"Analyzing '{uploaded_file.name}'... This may take a moment."):
        # Extract text from the PDF in memory
        nda_text = ""
        try:
            with fitz.open(stream=io.BytesIO(bytes_data), filetype="pdf") as doc:
                for page in doc:
                    nda_text += page.get_text("text") + "\n"
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")
            nda_text = None

        if nda_text:
            # Analyze the text to get the DataFrame with feedback
            results_df = analyze_nda_text(nda_text)

    # --- Display Results Directly on the Page ---
    st.subheader("Analysis Results")
    
    if results_df.empty:
        st.success("✅ All Clear! No major issues were found based on the playbook.")
    else:
        st.warning(f"🔍 Found {len(results_df)} items that may require your attention.")
        
        # Loop through the DataFrame rows and display each piece of feedback
        for index, row in results_df.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Category']}**")
                st.write(row['Recommendation'])
