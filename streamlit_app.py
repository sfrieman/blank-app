import streamlit as st
import fitz
import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, cellFormat, textFormat, set_column_width

# --- Paste your analyze_nda_text() function here (no changes needed) ---

def create_google_sheet(df, pdf_name):
    # This function is similar to the Cloud Function version
    try:
        # For Streamlit, you store secrets in their secrets manager
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        gc = gspread.authorize(creds)
        
        sheet_name = f"NDA First Review: {pdf_name}"
        sh = gc.create(sheet_name)
        # IMPORTANT: Share the sheet so the user can see it
        sh.share(None, perm_type='anyone', role='reader')
        
        worksheet = sh.sheet1
        if df.empty:
            worksheet.update([["Category", "Recommendation"], ["✅ No Issues Found", "This document appears to meet all standard requirements."]])
        else:
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        
        # Apply formatting...
        return sh.url
    except Exception as e:
        st.error(f"Error creating Google Sheet: {e}")
        return None

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
