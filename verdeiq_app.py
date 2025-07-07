import streamlit as st
import openai
import json
import os
import plotly.graph_objects as go

@st.cache_data
def load_questions():
    with open("esg_questions.json") as f:
        return json.load(f)

questions = load_questions()

openai.api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else os.getenv("OPENAI_API_KEY")

pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}

st.set_page_config(page_title="VerdeIQ | ESG Score for Startups", layout="centered")
st.title("🌿 VerdeIQ – ESG Readiness Score")
st.write("Answer 15 quick questions and get your GreenScore + AI-based ESG maturity tips")

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

    prompt = f"""
    A startup has the following ESG scores (0–5 scale):
    Environmental: {values[0]}
    Social: {values[1]}
    Governance: {values[2]}
    Provide 2 actionable, beginner-friendly improvement tips per pillar to help them improve ESG maturity.
    """

    try:
        with st.spinner("Generating ESG recommendations..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # ✅ Now using model available to all
                messages=[
                    {"role": "system", "content": "You are a helpful sustainability advisor for startups."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )
            recs = response["choices"][0]["message"]["content"]
            st.markdown("---")
            st.subheader("🔍 AI-Powered ESG Recommendations")
            st.markdown(recs)
    except Exception as e:
        st.error(f"Failed to generate recommendations: {e}")

    st.markdown("---")
    st.caption("Built by Hemaang Patkar using ESG Frameworks + Streamlit")
