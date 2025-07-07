import streamlit as st
import requests
import json
import os
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Score for Startups", layout="centered")

# --- Load Questions Safely ---
@st.cache_data
def load_questions():
    try:
        with open("esg_questions.json") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading questions: {e}")
        st.stop()

questions = load_questions()

# --- Session State ---
if "page" not in st.session_state:
    st.session_state.page = "intro"

# --- Introduction Page ---
if st.session_state.page == "intro":
    st.title("🌱 Welcome to VerdeIQ")
    st.subheader("Your ESG Readiness Companion for Startups")
    st.markdown("""
    ESG (Environmental, Social, Governance) practices reflect your startup's values,
    resilience, and long-term strategy. VerdeIQ helps you assess and improve these areas
    with a personalized ESG score and AI-generated insights.
    """)

    st.markdown("---")
    st.subheader("📋 Tell us about your company")
    company_name = st.text_input("Company Name")
    industry = st.text_input("Industry")
    company_size = st.selectbox("Company Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
    location = st.text_input("Headquarters Location")

    if st.button("Start ESG Assessment"):
        st.session_state.company_info = {
            "name": company_name,
            "industry": industry,
            "size": company_size,
            "location": location
        }
        st.session_state.page = "assessment"
        st.rerun()

# --- ESG Assessment Page ---
elif st.session_state.page == "assessment":
    st.title("📊 ESG Assessment")
    st.write("Answer a few quick questions to receive your GreenScore and tailored ESG tips.")

    responses = {}
    st.markdown("---")
    with st.form("esg_form"):
        for idx, q in enumerate(questions):
            st.markdown(f"**Q{idx+1}. {q['question']}**")
            responses[q["id"]] = st.radio("", options=q["options"], index=0, key=q["id"])
        submitted = st.form_submit_button("🚀 Get My ESG Score")

    if submitted:
        pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
        pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
        total_score = 0

        for q in questions:
            score = q["options"].index(responses[q["id"]])
            total_score += score
            pillar_scores[q["pillar"]] += score
            pillar_counts[q["pillar"]] += 1

        greenscore = round((total_score / (5 * len(questions))) * 100)
        st.success(f"🌿 Your GreenScore: **{greenscore}/100**")

        # --- Radar Chart ---
        labels = list(pillar_scores.keys())
        values = [pillar_scores[p] / pillar_counts[p] if pillar_counts[p] > 0 else 0 for p in labels]

        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name='ESG Maturity'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Personalized Prompt with Company Context ---
        info = st.session_state.company_info
        prompt = f"""
        You are an ESG advisor helping a startup improve its sustainability and governance.

        Company Details:
        - Name: {info['name']}
        - Industry: {info['industry']}
        - Size: {info['size']}
        - Location: {info['location']}

        Their ESG self-assessment scores (0–5 scale):
        - Environmental: {values[0]:.2f}
        - Social: {values[1]:.2f}
        - Governance: {values[2]:.2f}

        Provide 2 personalized and beginner-friendly improvement recommendations per pillar.
        Format:
        ### Environmental
        - Tip 1
        - Tip 2

        ### Social
        - Tip 1
        - Tip 2

        ### Governance
        - Tip 1
        - Tip 2
        """

        try:
            with st.spinner("Generating AI-powered ESG insights..."):
                cohere_api_key = st.secrets["cohere_api_key"]
                cohere_url = "https://api.cohere.ai/v1/chat"
                headers = {
                    "Authorization": f"Bearer {cohere_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "command-r-plus",
                    "message": prompt
                }
                response = requests.post(cohere_url, headers=headers, json=data)
                result = response.json()
                recs = result.get("text") or result.get("response") or "No recommendations received."
                st.markdown("---")
                st.subheader("🔍 AI-Powered ESG Recommendations")
                st.markdown(recs)
        except Exception as e:
            st.error(f"Failed to generate recommendations: {e}")

        st.markdown("---")
        st.download_button("📥 Download My ESG Report", data=json.dumps({
            "company": info,
            "score": greenscore,
            "pillar_scores": dict(zip(labels, values)),
            "answers": responses
        }, indent=2), file_name="verdeiq_esg_report.json", mime="application/json")

        st.caption("Crafted by Hemaang Patkar using Streamlit + Cohere + ESG Frameworks")
