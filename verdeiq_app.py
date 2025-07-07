import streamlit as st
import requests
import json
import os
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Score for Startups", layout="centered")

@st.cache_data
def load_questions():
    try:
        with open("esg_questions.json") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading questions: {e}")
        st.stop()

questions = load_questions()

# Split questions by pillar
env_questions = [q for q in questions if q['pillar'] == 'Environmental']
soc_questions = [q for q in questions if q['pillar'] == 'Social']
gov_questions = [q for q in questions if q['pillar'] == 'Governance']

# --- Session State Management ---
if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.company_info = {}

# --- Intro Page ---
if st.session_state.page == "intro":
    st.title("Welcome to VerdeIQ")
    st.subheader("Make Your Startup ESG-Ready")
    st.markdown("""
    VerdeIQ is your sustainability companion. ESG—Environmental, Social, and Governance—are global standards that help assess an organization's ethics, impact, and resilience.

    Built on GRI, SASB, BRSR & UN SDGs frameworks
    Personalized AI recommendations
    Visual ESG Maturity Radar

    We’ll ask you a few simple questions and tailor your journey.
    """)

    st.markdown("---")
    st.subheader("Company Details")
    st.session_state.company_info['name'] = st.text_input("Company Name")
    st.session_state.company_info['industry'] = st.text_input("Industry")
    st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
    st.session_state.company_info['location'] = st.text_input("Location (City, Country)")
    st.session_state.company_info['esg_goals'] = st.multiselect("What are your current ESG focus areas?", ["Carbon Neutrality", "DEI (Diversity, Equity, Inclusion)", "Data Privacy", "Compliance", "Community Engagement", "Green Reporting"])

    if st.button("Start Environmental Assessment →"):
        st.session_state.page = "env"
        st.rerun()

# --- Environmental Page ---
elif st.session_state.page == "env":
    st.title("Environmental Readiness")
    with st.form("env_form"):
        for q in env_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
        if st.form_submit_button("Next: Social →"):
            st.session_state.page = "soc"
            st.rerun()

# --- Social Page ---
elif st.session_state.page == "soc":
    st.title("Social Impact Readiness")
    with st.form("soc_form"):
        for q in soc_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
        if st.form_submit_button("Next: Governance →"):
            st.session_state.page = "gov"
            st.rerun()

# --- Governance Page ---
elif st.session_state.page == "gov":
    st.title("Governance Structure Readiness")
    with st.form("gov_form"):
        for q in gov_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
        if st.form_submit_button("Get Final ESG Report →"):
            st.session_state.page = "results"
            st.rerun()

# --- Results Page ---
elif st.session_state.page == "results":
    responses = st.session_state.responses
    info = st.session_state.company_info

    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
    total_score = 0

    for q in questions:
        score = q["options"].index(responses[q["id"]])
        total_score += score
        pillar_scores[q["pillar"]] += score
        pillar_counts[q["pillar"]] += 1

    greenscore = round((total_score / (5 * len(questions))) * 100)
    st.title("Your ESG Summary Report")
    st.success(f"GreenScore: **{greenscore}/100**")

    labels = list(pillar_scores.keys())
    values = [pillar_scores[p] / pillar_counts[p] if pillar_counts[p] > 0 else 0 for p in labels]
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself', name='ESG Maturity'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    prompt = f"""
    You are an expert ESG advisor helping a startup with tailored advice.

    Company Details:
    - Name: {info['name']}
    - Industry: {info['industry']}
    - Size: {info['size']}
    - Location: {info['location']}
    - ESG Priorities: {', '.join(info['esg_goals']) if info['esg_goals'] else 'None specified'}

    Self-assessment scores (0–5 scale):
    - Environmental: {values[0]:.2f}
    - Social: {values[1]:.2f}
    - Governance: {values[2]:.2f}

    Provide personalized, beginner-friendly recommendations referencing real frameworks like GRI, SASB, SDGs, or BRSR.
    """

    try:
        with st.spinner("Generating your ESG guidance..."):
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
            st.subheader("ESG Framework-Based Recommendations")
            st.markdown(recs)
    except Exception as e:
        st.error(f"Failed to generate recommendations: {e}")

    st.download_button("Download My ESG Report", data=json.dumps({
        "company": info,
        "score": greenscore,
        "pillar_scores": dict(zip(labels, values)),
        "answers": responses
    }, indent=2), file_name="verdeiq_esg_report.json", mime="application/json")

    st.caption("Crafted by Hemaang Patkar")
