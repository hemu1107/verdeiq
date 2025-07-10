# --- Enhanced VerdeIQ ESG Assessment App with PDF Export & AI Insights ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from fpdf import FPDF
import tempfile

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Styling & Theming ---
st.markdown("""
    <style>
        .title-style {font-size: 32px; font-weight: bold; color: #228B22;}
        .section-title {font-size: 20px; font-weight: 600; margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- Load ESG Questions JSON ---
@st.cache_data
def load_questions():
    file_path = Path("esg_questions.json")
    if not file_path.exists():
        st.error("Questions file not found.")
        st.stop()
    with open(file_path) as f:
        return json.load(f)

questions = load_questions()

# --- Split by Pillar ---
def categorize_questions(questions):
    env = [q for q in questions if q['pillar'] == 'Environmental']
    soc = [q for q in questions if q['pillar'] == 'Social']
    gov = [q for q in questions if q['pillar'] == 'Governance']
    return env, soc, gov

env_questions, soc_questions, gov_questions = categorize_questions(questions)

# --- Session Management ---
if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.company_info = {}

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Crafted by Hemaang Patkar | ESG Intelligence Platform")
    st.markdown("""
    VerdeIQ is your AI-powered ESG self-assessment and intelligence tool.

    - 💡 Answer core ESG questions across Environmental, Social & Governance pillars
    - 📊 Get instant maturity score & badge
    - 🌍 Align with frameworks: **GRI**, **SASB**, **BRSR**, **TCFD**, **UN SDGs**
    - 🧠 Receive Cohere-powered expert ESG recommendations
    - 📄 Download your insights as a professional PDF report

    **Maturity Tiers:**
    - 🌱 Seedling (0–29)
    - 🌿 Sprout (30–49)
    - 🍃 Developing (50–69)
    - 🌳 Mature (70–89)
    - ✨ Leader (90–100)
    """)
    if st.button("Start ESG Assessment ➔"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Organization Profile")
    with st.form("org_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.company_info['name'] = st.text_input("Company Name")
            st.session_state.company_info['industry'] = st.text_input("Industry")
            st.session_state.company_info['location'] = st.text_input("City")
            st.session_state.company_info['external_esg_rating'] = st.text_input("External ESG Rating (if any)")
            st.session_state.company_info['esg_reporting_freq'] = st.selectbox("ESG Reporting Frequency", ["Monthly", "Quarterly", "Annually", "Not Yet"])
        with c2:
            st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
            st.session_state.company_info['esg_goals'] = st.multiselect("Key ESG Priorities", ["Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"])
            st.session_state.company_info['public_status'] = st.radio("Is your company publicly listed?", ["Yes", "No", "Planning to"])
            st.session_state.company_info['region'] = st.selectbox("Primary Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"])
        st.session_state.company_info['years_operating'] = st.slider("Years in Operation", 0, 100, 5)
        st.session_state.company_info['supply_chain_scope'] = st.selectbox("Supply Chain ESG Coverage", ["None", "Tier-1 Vendors", "Tier 1 & 2", "End-to-End"])
        st.session_state.company_info['data_collection_tool'] = st.text_input("Tool/Software used for ESG Data Collection")
        st.session_state.company_info['sustainability_officer'] = st.text_input("Chief Sustainability Officer (if any)")

        if st.form_submit_button("Proceed to Assessment ➔"):
            st.session_state.page = "env"
            st.rerun()

elif st.session_state.page == "env":
    st.header("Environment 🌿")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.form_submit_button("Next: Social ➔"):
            st.session_state.page = "soc"
            st.rerun()

elif st.session_state.page == "soc":
    st.header("Social 🤝")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.form_submit_button("Next: Governance ➔"):
            st.session_state.page = "gov"
            st.rerun()

elif st.session_state.page == "gov":
    st.header("Governance 🏛️")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.form_submit_button("✔️ View My ESG Results"):
            st.session_state.page = "results"
            st.rerun()
