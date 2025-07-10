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

# --- Helper Functions ---
def show_question_block(q, idx, total):
    st.markdown(f"**{q['id']}: {q['question']}**")
    if q.get('frameworks'):
        st.caption(f"Frameworks: {', '.join(q['frameworks'])}")
    st.session_state.responses[q['id']] = st.radio(
        label=f"Question {idx + 1} of {total}",
        options=q['options'],
        index=0,
        key=q['id']
    )
    st.markdown("---")

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

# ... [UNCHANGED CODE: DETAILS, ENV, SOC, GOV PAGES] ...

elif st.session_state.page == "results":
    st.title("🌿 ESG Assessment Results")

    def calculate_scores(responses):
        pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
        pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
        total_score = 0

        for q in questions:
            score = q["options"].index(responses[q["id"]])
            total_score += score
            pillar_scores[q["pillar"]] += score
            pillar_counts[q["pillar"]] += 1

        verde_score = round((total_score / (5 * len(questions))) * 100)
        return verde_score, pillar_scores, pillar_counts

    verde_score, scores, counts = calculate_scores(st.session_state.responses)
    labels = list(scores.keys())
    values = [scores[k] / counts[k] if counts[k] else 0 for k in labels]

    st.metric(label="Verde Score", value=f"{verde_score}/100")
    badge = "🌱 Seedling" if verde_score < 30 else "🌿 Sprout" if verde_score < 50 else "🍃 Developing" if verde_score < 70 else "🌳 Mature" if verde_score < 90 else "✨ Leader"
    st.success(f"Badge Level: {badge}")

    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Crafted by Hemaang Patkar")

    # --- Generate Prompt ---
    info = st.session_state.company_info
    responses = st.session_state.responses
    detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])

    prompt = f"""
You are an expert Senior ESG Consultant with 25+ years of experience advising companies globally on sustainability strategies, regulatory compliance, and ESG transformation. Your task is to generate a personalized, data-backed ESG Assessment Report and Strategic Roadmap for the following company. This report should feel like a $25,000+ consulting engagement, tailored for CXOs, investors, and ESG leads.

🏢 **Company Overview**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Size: {info.get('size')}
- Ownership: {info.get('public_status')}
- Region: {info.get('region')}
- Years Operating: {info.get('years_operating')} years
- ESG Focus Areas: {', '.join(info.get('esg_goals', [])) or 'Not specified'}

📊 **VerdeIQ Assessment Summary**
- *Verde Score*: {verde_score}/100
- *Environmental Maturity*: {values[0]:.2f}/5
- *Social Maturity*: {values[1]:.2f}/5
- *Governance Maturity*: {values[2]:.2f}/5

🧠 **Assessment Responses**
{detailed_answers}

---

🎯 **Deliver the following sections in markdown format**:
1. ESG Summary and Risk Profile
2. Strategic ESG Roadmap
3. Pillar-Wise Maturity Evaluation
4. Toolkits, Templates, and Digital Aids
5. Case Study Analogues
6. Key KPIs and Milestones
7. Implementation Risk Assessment
8. Strategic Call-to-Action
"""

    # --- Call Cohere API ---
    st.subheader("📓 Premium ESG Recommendations")
    with st.spinner("Generating expert ESG roadmap..."):
        cohere_api_key = st.secrets.get("cohere_api_key")
        if cohere_api_key:
            response = requests.post(
                url="https://api.cohere.ai/v1/chat",
                headers={"Authorization": f"Bearer {cohere_api_key}", "Content-Type": "application/json"},
                json={"model": "command-r-plus", "message": prompt}
            )
            output = response.json()
            recs = output.get("text") or output.get("response") or "No response received."
            st.markdown(recs)
        else:
            st.warning("Cohere API key not found in secrets.")
