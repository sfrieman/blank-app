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

               # Attorney’s Fees
        if not re.search(r"attorney", nda_text, re.IGNORECASE):
            feedback.append(["Attorney’s Fees", "Insert:\n\n In the event of a final, non-appealable order issued by a court of competent jurisdiction in a dispute between the parties relating to this [Agreement], the non-prevailing party shall pay all costs and expenses, including, but not limited to, reasonable outside attorneys' fees, relating thereto.\n\n"])

        # Notices
        notice_patterns = [
            r"provided that a copy of any notice sent to \[Company\] shall be sent by email",
            r"provided that a copy of all notices sent to legal@capsule\.com",
            r"Notices shall be sent to the addresses set forth at the end of this Agreement",
            r"copy of any notice sent to \[Company\] shall be sent to \[Company\] by email"
        ]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in notice_patterns):
            feedback.append(["Notices", "Insert:\n\n Notices shall be sent to the addresses set forth at the end of this [Agreement] or such other address as either party may specify in writing.\n\n"])

        # Confidential Information
        required_terms = ["affiliates", "suppliers", "customers", "employees"]
        missing_terms = [term for term in required_terms if not re.search(r"\b" + re.escape(term) + r"\b", nda_text, re.IGNORECASE)]

        if missing_terms:
            feedback.append([
                "Confidential Information",
                (f"Ensure that 'Confidential Information' includes information of [Discloser] or its affiliates, customers, suppliers, or employees.\n\n Missing terms: {', '.join(missing_terms)}\n\n")
            ])

        # Representatives
        representatives_info_patterns = [
            r"Representatives must include directors, officers, employees, independent contractors",
        ]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in representatives_info_patterns):
            feedback.append(["Representatives", "Ensure comprehensive definition of Representatives:\n\n The [Receiving Party] may disclose Confidential Information to directors, officers, employees, independent contractors, advisors, and agents who are apprised of the confidential nature of the Confidential Information and all of the restrictions in this [Agreement], and have signed a written agreement with [Receiving Party] containing confidentiality and non-use restrictions at least as protective as those of this [Agreement].\n\n"])

        # Legal Requirement
        legal_requirement_patterns = [
            r"Nothing in this Agreement prevents either Party from complying with any law, regulation, court order, stock exchange requirement, legal process or other legal requirement",
            r"complying with any law, regulation, court order"
        ]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in legal_requirement_patterns):
            feedback.append(["Legal Requirement", "Legal Requirement must be a defined term. Insert or include these qualifiers:\n\n Nothing in this [Agreement] prevents either [Party] from complying with any law, regulation, court order, stock exchange requirement, legal process or other legal requirement (“Legal Requirement”) that compels disclosure of any [Confidential Information]; provided, that [Recipient] will, if legally permissible, promptly notify [Company] upon learning of any such Legal Requirement and will reasonably cooperate with [Company], at the [Companys] request and sole expense, in the exercise of its right to seek to protect the confidentiality of the Confidential Information before any tribunal or governmental agency.\n\n"])

        protective_order_pattern = r"protective order\)"
        if not re.search(protective_order_pattern, nda_text, re.IGNORECASE):
            feedback.append(["Legal Requirement", "Insert:\n\n [Disclosing Party] may seek a protective order or other appropriate remedy (at their sole cost and expense).\n\n"])

        # AS IS & No Licenses
        no_warranties_patterns = [r"All Confidential Information is provided “AS IS.”", r"“AS IS.”"]
        no_licenses_pattern = r"right or license"

        has_warranties = any(re.search(p, nda_text, re.IGNORECASE) for p in no_warranties_patterns)
        has_licenses = re.search(no_licenses_pattern, nda_text, re.IGNORECASE)

        if not has_warranties:
             feedback.append(["\"AS IS\"", "Insert:\n\n All Confidential Information is provided 'AS IS.' [Disclosing Party] will not be liable to [Receiving Party] or any of its affiliates for damages arising from any use of the Confidential Information or from errors, omissions or otherwise.\n\n"])

        if not has_licenses:
            feedback.append(["No Warranties or Licenses", "Insert:\n\n Neither this [Agreement], nor any disclosure of Confidential Information hereunder grants to [Receiving Party] any right or license under any copyright, patent, mask work, trade secret or other intellectual property right, except solely for the use expressly permitted herein.\n\n"])

        # Term
        if "Term" in nda_text:
            feedback.append(["Term", "Keep the term from 1 to 5 years. Always avoid indefinite terms unless absolutely necessary. Trade secrets can have separate terms.\n\n"])

        # Return or Destruction of Materials
        combined_return_pattern = (
            r"(?is)"
            r"(?=.*\bretain\b)"
            r"(?=.*\bcopy\b)"
            r"(?=.*\bconfidential\b)"
            r"(?=.*\brestricted\s+access\b)"
            r"(?=.*\b(?:legal|archival|backup)\b)"
            r"(?=.*\b(?:choose|option|decide|discretion)\b)"
            r"(?=.*\breturn\b)"
            r"(?=.*\bdestroy(?:\b|tion\b))"
        )
        if not re.search(combined_return_pattern, nda_text):
            feedback.append([
                "Return or Destruction of Materials",
                ("Insert a clause addressing the return or destruction of materials with exceptions for legal/archival purposes.\n\n"
                    "For example:\n\n[Receiving Party] and its [Representatives] (i) may retain one copy of such materials...\n\n"
                    "...in the confidential, restricted access files of its legal department for use only in the event of a dispute\n\n"
                    "...related to the [Purpose] or as required by applicable law, and (ii) shall have the option to decide whether\n\n"
                    "...to return or destroy such materials, with electronic copies created pursuant to automatic archival or backup procedures\n\n"
                    "...being excluded from deletion.\n\n")
            ])

        # Breach or Threatened Breach
        breach_clause = r"irreparable harm.*breach or threatened breach.*without the necessity of posting any bond"
        if not re.search(breach_clause, nda_text, re.IGNORECASE | re.DOTALL):
            feedback.append(["Breach or Threatened Breach", "Insert:\n\n The [Receiving Party] acknowledges that monetary damages may not be a sufficient remedy for irreparable harm caused by any breach or threatened breach of this [Agreement], and the [Disclosing Party] is entitled to seek an injunction or other similar equitable remedies without the necessity of posting any bond or showing such irreparable harm.\n\n"])

        # Assignments
        assignment_patterns = [
            r"This Agreement will not be assigned by either party without the prior written consent of the other",
            r"This Agreement will not be assigned",
            r"assign"
        ]
        if not any(re.search(p, nda_text, re.IGNORECASE) for p in assignment_patterns):
            feedback.append(["Assignments", "Insert:\n\n This [Agreement] will not be assigned by either party without the prior written consent of the other, not to be unreasonably withheld; provided that without notice or consent this [Agreement] may be assigned to a successor of such party by purchase, merger, or consolidation.\n\n"])


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
