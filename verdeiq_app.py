import streamlit as st
import requests
import json
import os
import plotly.graph_objects as go

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Score for Organizations", layout="centered")

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
    st.subheader("Measure and Enhance Your ESG Maturity")
    st.markdown("""
    **What is VerdeIQ?**

    - *VerdeIQ* is an AI-powered ESG Assessment Tool for organizations whether startups, SMEs, or enterprises. 
    - The word **Verde** means *Green* in Spanish, symbolizing our commitment to sustainability. 
    - *VerdeIQ* represents *Green Intelligence*—insightful, data-backed ESG action.

    **How It Works**
    - Answer these core 15 curated questions across Environmental, Social and Governance (ESG) pillars
    - Receive a **Verde Score (0–100)** based on your practices
    - Get AI-powered recommendations using **GRI**, **SASB**, **BRSR** & other related frameworks

    **Verde Score Badge System**
    - 🌱 **Seedling (0–29)** – Early-stage awareness
    - 🌿 **Sprout (30–49)** – Laying the foundation
    - 🍃 **Developing (50–69)** – Making visible progress
    - 🌳 **Mature (70–89)** – Strategic implementation
    - 🌟 **Leader (90–100)** – Best-in-class ESG
    """)
    if st.button("Continue →"):
        st.session_state.page = "details"
        st.rerun()

# --- Company Details Page ---
elif st.session_state.page == "details":
    st.title("🏢 Organization Details")
    st.session_state.company_info['name'] = st.text_input("Organization Name")
    st.session_state.company_info['industry'] = st.text_input("Industry")
    st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
    st.session_state.company_info['location'] = st.text_input("Location (City)")
    st.session_state.company_info['esg_goals'] = st.multiselect("Current ESG focus areas", ["Carbon Neutrality", "DEI (Diversity, Equity, Inclusion)", "Data Privacy", "Compliance", "Community Engagement", "Green Reporting"])
    if st.button("Start Assessment →"):
        st.session_state.page = "env"
        st.rerun()

# --- Environmental Page ---
elif st.session_state.page == "env":
    st.title("🌿 Environmental Readiness")
    st.markdown("""
    This section assesses your environmental practices: emissions, energy use, water, waste and sustainability strategy.
    """)
    with st.form("env_form"):
        for q in env_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
            st.markdown("---")
        if st.form_submit_button("Next: Social Assessment →"):
            st.session_state.page = "soc"
            st.rerun()

# --- Social Page ---
elif st.session_state.page == "soc":
    st.title("🤝 Social Impact Readiness")
    st.markdown("""
    This section explores how you approach team well-being, diversity, equity, inclusion, training and community involvement.
    """)
    with st.form("soc_form"):
        for q in soc_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
            st.markdown("---")
        if st.form_submit_button("Next: Governance Assessment →"):
            st.session_state.page = "gov"
            st.rerun()

# --- Governance Page ---
elif st.session_state.page == "gov":
    st.title("🏛️ Governance Structure Readiness")
    st.markdown("""
    Evaluate your leadership integrity, compliance practices, board structure and information security.
    """)
    with st.form("gov_form"):
        for q in gov_questions:
            st.markdown(f"**{q['id']}: {q['question']}**")
            frameworks = ', '.join(q.get('frameworks', []))
            st.caption(f"Frameworks: {frameworks}" if frameworks else "")
            st.session_state.responses[q['id']] = st.radio("", q['options'], index=0, key=q['id'])
            st.markdown("---")
        if st.form_submit_button("Get My ESG Analysis →"):
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

    verde_score = round((total_score / (5 * len(questions))) * 100)
    st.title("🎯 Your ESG Summary Report")
    st.success(f"Verde Score: **{verde_score}/100**")

    if verde_score < 30:
        grade = "🌱 Seedling"
    elif verde_score < 50:
        grade = "🌿 Sprout"
    elif verde_score < 70:
        grade = "🍃 Developing"
    elif verde_score < 90:
        grade = "🌳 Mature"
    else:
        grade = "🌟 Leader"

    st.info(f"Badge: **{grade}**")

    labels = list(pillar_scores.keys())
    values = [pillar_scores[p] / pillar_counts[p] if pillar_counts[p] > 0 else 0 for p in labels]
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself', name='ESG Maturity'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    prompt = f"""
    You are an expert Senior ESG Consultant Advisor helping a company with tailored advice.

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

    Provide personalized, industry grade recommendations referencing real frameworks like GRI, SASB, SDGs, or BRSR.
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
            st.subheader("📚 ESG Framework-Based Recommendations")
            st.markdown(recs)
    except Exception as e:
        st.error(f"Failed to generate recommendations: {e}")

    st.download_button("📥 Download My ESG Report", data=json.dumps({
        "company": info,
        "score": verde_score,
        "grade": grade,
        "pillar_scores": dict(zip(labels, values)),
        "answers": responses
    }, indent=2), file_name="verdeiq_esg_report.json", mime="application/json")

    st.caption("Crafted by Hemaang Patkar")
