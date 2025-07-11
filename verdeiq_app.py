# --- Enhanced VerdeIQ ESG Assessment App with Agentic AI Persona ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path

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

# --- Agentic Copilot Introduction ---
def introduce_agent():
    st.info("🤖 Meet VerdeBot: Your ESG Copilot")
    st.caption("VerdeBot will guide you through the ESG assessment journey, adaptively interpreting your inputs to generate strategic insights aligned with global standards.")

# --- Helper Functions ---
def show_question_block(q, idx, total):
    st.markdown(f"**{q['id']}: {q['question']}**")
    if q.get('frameworks'):
        st.caption(f"Frameworks: {', '.join(q['frameworks'])}")
    st.session_state.responses[q['id']] = st.radio(
        label=f"Agentic Analysis {idx + 1} of {total}",
        options=q['options'],
        index=0,
        key=q['id']
    )
    st.markdown("---")

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

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Your Agentic ESG Copilot")
    st.caption("Crafted by Hemaang Patkar")
    introduce_agent()
    st.markdown("""
    VerdeIQ simulates the behavior of a real-world ESG consultant — not just scoring, but analyzing, advising, and adapting.

    - 🤖 Agentic Persona: VerdeBot interprets your responses
    - 🔎 15 ESG-aligned prompts mapped to global frameworks
    - 📊 Real-time contextual scoring and advisory
    - 🛍️ Roadmaps curated to your company’s size, maturity, and sector

    **Maturity Tiers:**
    - 🌱 Seedling (0–29)
    - 🌿 Sprout (30–49)
    - 🍃 Developing (50–69)
    - 🌳 Mature (70–89)
    - ✨ Leader (90–100)
    """)
    if st.button("Launch ESG Copilot →"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Agentic Profile Setup")
    st.caption("VerdeBot is learning your company DNA...")
    with st.form("org_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.company_info['name'] = st.text_input("Company Name")
            st.session_state.company_info['industry'] = st.text_input("Industry")
            st.session_state.company_info['location'] = st.text_input("City")
            st.session_state.company_info['supply_chain_exposure'] = st.selectbox("Supply Chain Exposure", ["Local", "Regional", "Global"])
            st.session_state.company_info['carbon_disclosure'] = st.radio("Discloses Carbon Emissions?", ["Yes", "No"])
            st.session_state.company_info['third_party_audits'] = st.radio("Undergoes 3rd-Party ESG Audits?", ["Yes", "No", "Planned"])
            st.session_state.company_info['stakeholder_reporting'] = st.radio("Publishes Stakeholder Reports?", ["Yes", "No"])
            st.session_state.company_info['materiality_assessment_status'] = st.radio("Materiality Assessment Conducted?", ["Yes", "No", "In Progress"])
            st.session_state.company_info['board_esg_committee'] = st.radio("Board-Level ESG Committee?", ["Yes", "No"])
        with c2:
            st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"])
            st.session_state.company_info['esg_goals'] = st.multiselect("Core ESG Intentions", [
                "Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"])
            st.session_state.company_info['public_status'] = st.radio("Listed Status", ["Yes", "No", "Planning to"])
            st.session_state.company_info['sector_type'] = st.radio("Sector Type", ["Manufacturing", "IT/Services", "Finance", "Healthcare", "Other"])
            st.session_state.company_info['esg_team_size'] = st.selectbox("Dedicated ESG Team Size", ["0", "1-2", "3-5", "6-10", "10+"])
            st.session_state.company_info['internal_esg_training'] = st.radio("Internal ESG Training Programs?", ["Yes", "No"])
            st.session_state.company_info['climate_risk_policy'] = st.radio("Climate Risk Mitigation Policy?", ["Yes", "No"])
            st.session_state.company_info['regulatory_exposure'] = st.selectbox("Regulatory Exposure", ["Low", "Moderate", "High"])

        st.session_state.company_info['region'] = st.selectbox("Main Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"])
        st.session_state.company_info['years_operating'] = st.slider("Years Since Founding", 0, 200, 5)

        if st.form_submit_button("Activate ESG Analysis →"):
            st.session_state.page = "env"
            st.rerun()

# (Remaining code continues unchanged)


elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    st.caption("VerdeBot is interpreting your sustainability posture...")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.form_submit_button("Continue to Social 🤝"):
            st.session_state.page = "soc"
            st.rerun()

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    st.caption("Analyzing your team, culture, and external impact...")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.form_submit_button("Continue to Governance 🏛️"):
            st.session_state.page = "gov"
            st.rerun()

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    st.caption("Parsing leadership ethics and oversight structures...")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.form_submit_button("Generate Agentic Summary ✨"):
            st.session_state.page = "results"
            st.rerun()

elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Agentic ESG Summary")
    verde_score, scores, counts = calculate_scores(st.session_state.responses)
    labels = list(scores.keys())
    values = [scores[k] / counts[k] if counts[k] else 0 for k in labels]

    badge = "🌱 Seedling" if verde_score < 30 else \
            "🌿 Sprout" if verde_score < 50 else \
            "🍃 Developing" if verde_score < 70 else \
            "🌳 Mature" if verde_score < 90 else "✨ Leader"

    st.metric(label="Your ESG Copilot Score", value=f"{verde_score}/100")
    st.success(f"Agentic Tier: {badge}")

    st.caption("VerdeBot interprets your ESG behavior across the three strategic pillars. Here's your performance radar:")
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- Agentic Recommendation Generator ---
    if st.button("🔍 Generate My ESG Roadmap (via VerdeBot)"):
        with st.spinner("VerdeBot is analyzing your profile and responses..."):
            try:
                info = st.session_state.company_info
                responses = st.session_state.responses
                detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])
                prompt = f"""You are VerdeBot, an advanced Agentic ESG Copilot and strategic advisor with deep expertise in global sustainability practices, regulatory alignment, and corporate governance. Your role is to act as a senior ESG consultant tasked with translating the following company’s ESG posture into a precise, framework-aligned, and context-aware roadmap.

Approach this with the analytical rigor of a McKinsey or BCG ESG lead, blending technical sustainability metrics with industry-specific insights. Ensure your output is:
- Aligned with frameworks such as GRI, SASB, BRSR, and UN SDGs.
- Professional and jargon-savvy — suitable for boardrooms, investors, and compliance officers.
- Specific to inputs — DO NOT hallucinate metrics or add fluffy generalities.

---

🏢 **Company Profile**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Sector Type: {info.get('sector_type')}
- Team Size: {info.get('size')}
- ESG Team Size: {info.get('esg_team_size')}
- Public Status: {info.get('public_status')}
- Region: {info.get('region')}
- Years in Operation: {info.get('years_operating')}
- Main City: {info.get('location')}
- Operational Reach: {info.get('supply_chain_exposure')}
- Regulatory Risk Level: {info.get('regulatory_exposure')}
- Core ESG Intentions: {', '.join(info.get('esg_goals', [])) or 'Not specified'}

📄 **Governance & Policy Indicators**
- Materiality Assessment: {info.get('materiality_assessment_status')}
- ESG Board Committee: {info.get('board_esg_committee')}
- Climate Risk Policy: {info.get('climate_risk_policy')}
- Internal ESG Training: {info.get('internal_esg_training')}
- Carbon Disclosure: {info.get('carbon_disclosure')}
- Third-Party ESG Audits: {info.get('third_party_audits')}
- Stakeholder Reporting: {info.get('stakeholder_reporting')}

📊 **Assessment Results**
- VerdeIQ Score: {verde_score}/100
- Badge: {badge}
- Environmental Maturity: {values[0]:.2f}/5
- Social Maturity: {values[1]:.2f}/5
- Governance Maturity: {values[2]:.2f}/5

🧠 **Self-Assessment Snapshot**
{detailed_answers}

---

🎯 **Your Task as VerdeBot**

Deliver a structured and deeply tailored ESG Advisory Report. Structure it with the following sections:

1. **ESG Profile Summary**
   - Showcase strengths across the 3 pillars based on maturity scores and profile fields.
   - Identify 3–5 gaps considering disclosures, governance, training, and risk.
   - Reference ESG frameworks like GRI 305, SASB Standards, BRSR Principle 3, SDG 12, etc.

2. **Roadmap (0–36 Months)**
   - **Immediate (0–6 months):** Internal capacity-building, audits, dashboards, materiality clarifications.
   - **Mid-Term (6–18 months):** Stakeholder engagement, GRI-aligned reporting, risk-based action plans.
   - **Long-Term (18–36 months):** Third-party disclosures, ESG ratings readiness, governance reform.

3. **Pillar-Wise Breakdown**
   - 2–3 recommendations per pillar.
   - Tie each point to global ESG frameworks and relevant tools.

4. **Tools & Metrics**
   - Suggest tools, templates, and documents to use immediately (aligned to company maturity).
   - E.g., CDP portal, SASB Navigator, DEI dashboards, ESG risk register.

5. **90-Day Advisory Plan**
   - List 4–5 tactical, confidence-building actions.

---

🔒 Close by saying:
“This roadmap was synthesized by VerdeBot — your intelligent ESG copilot engineered to embed sustainability into strategy, purpose into performance.”
"""

                cohere_api_key = st.secrets.get("cohere_api_key")
                if cohere_api_key:
                    response = requests.post(
                        url="https://api.cohere.ai/v1/chat",
                        headers={
                            "Authorization": f"Bearer {cohere_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={"model": "command-r-plus", "message": prompt}
                    )
                    output = response.json()
                    recs = output.get("text") or output.get("response") or "No response received."
                    st.subheader("📓 VerdeBot's Strategic ESG Roadmap")
                    st.markdown(recs)
                else:
                    st.warning("⚠️ Cohere API key not found. Please add it to your secrets config.")

            except Exception as e:
                st.error(f"❌ Error generating roadmap: {e}")
