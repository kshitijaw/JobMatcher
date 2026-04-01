# StreamLit UI

import streamlit as st
import pdfplumber, io
from database import init_db, add_subscriber

init_db()

st.title("🔍 Job Alert — Subscribe")
st.caption("Get hourly LinkedIn job matches sent to your email.")

col1, col2 = st.columns(2)
with col1:
    role = st.text_input("Job Role", placeholder="e.g. Data Engineer")
with col2:
    city = st.text_input("City", placeholder="e.g. Bengaluru")

email = st.text_input("Email", placeholder="you@example.com")

uploaded = st.file_uploader("Resume (PDF)", type=["pdf"])
resume_text = ""
if uploaded:
    with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
        resume_text = "\n".join(p.extract_text() or "" for p in pdf.pages).strip()
    st.caption(f"✓ {len(resume_text):,} characters extracted")

col1, col2, col3 = st.columns([1.5, 2, 1.5])
with col2:
    if st.button("Subscribe to Job Alerts", type="primary", use_container_width=True):
        if not all([role, city, email, resume_text]):
            st.error("All fields are required.")
            
        elif "@" not in email:
            st.error("Enter a valid email.")
        else:
            add_subscriber(email, role, city, resume_text)
            st.success(f"Subscribed! You'll get job alerts at **{email}** every hour.")
