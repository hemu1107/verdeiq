
import streamlit as st
import requests
import json
import os
import plotly.graph_objects as go

@st.cache_data
def load_questions():
    with open("esg_questions.json") as f:
        return json.load(f)

questions = load_questions()

pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}

st.set_page_config(page_title="VerdeIQ | ESG Score for Startups", layout="centered")
st.title("🌿 VerdeIQ – ESG Readiness Score")
st.write("Answer a few quick questions and get your GreenScore + AI-based ESG maturity tips")

responses = {}
st.markdown("---")
with st.form("esg_form"):
    for q in questions:
        response = st.radio(
            f"**{q['question']}**",
            options=q["options"],
            index=0,
            key=q["id"]
        )
        responses[q["id"]] = response
    submitted = st.form_submit_button("🚀 Get My ESG Score")

if submitted:
    total_score = 0
    for q in questions:
        selected_option = responses[q["id"]]
        score = q["options"].index(selected_option)
        total_score += score
        pillar_scores[q["pillar"]] += score
        pillar_counts[q["pillar"]] += 1

    greenscore = round((total_score / (5 * len(questions))) * 100)
    st.success(f"Your GreenScore: **{greenscore}/100**")

    labels = list(pillar_scores.keys())
    values = [pillar_scores[p] / pillar_counts[p] for p in labels]

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

    prompt = f"A startup has these ESG scores (0–5 scale):\nEnvironmental: {values[0]}\nSocial: {values[1]}\nGovernance: {values[2]}\nProvide 2 beginner-friendly improvement tips per pillar to improve ESG maturity."

    try:
        with st.spinner("Generating ESG recommendations via Cohere..."):
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
            recs = result.get("text") or result.get("response") or "No recommendation received."
            st.markdown("---")
            st.subheader("🔍 AI-Powered ESG Recommendations")
            st.markdown(recs)
    except Exception as e:
        st.error(f"Failed to generate recommendations: {e}")

    st.markdown("---")
    st.caption("Built with ❤️ by Hemaang Patkar using Cohere + ESG Frameworks + Streamlit")
