# --- Enhanced VerdeIQ ESG Assessment App (with Feedback Enhancements) ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Styling ---
st.markdown("""
    <style>
        .title-style {font-size: 32px; font-weight: bold; color: #228B22;}
        .section-title {font-size: 20px; font-weight: 600; margin-top: 20px;}
        .badge-green {color: green; font-weight: bold;}
        .badge-yellow {color: orange; font-weight: bold;}
        .badge-red {color: red; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Navigation ---
pages = ["intro", "details", "env", "soc", "gov", "review", "results"]
titles = {
    "intro": "🌱 Welcome",
    "details": "🏢 Company Info",
    "env": "🌿 Environmental",
    "soc": "🤝 Social",
    "gov": "🏛️ Governance",
    "review": "🔍 Review",
    "results": "📊 Results"
}

if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.company_info = {}

with st.sidebar:
    st.markdown("## 🧭 Navigation")
    for p in pages:
        if p == st.session_state.page:
            st.markdown(f"**➤ {titles[p]}**")
        elif p in pages[:pages.index(st.session_state.page)]:  # Allow back navigation
            if st.button(titles[p]):
                st.session_state.page = p
                st.rerun()

# --- Load Questions ---
@st.cache_data
def load_questions():
    file_path = Path("esg_questions.json")
    if not file_path.exists():
        st.error("Questions file not found.")
        st.stop()
    with open(file_path) as f:
        return json.load(f)

questions = load_questions()

def categorize_questions(questions):
    env = [q for q in questions if q['pillar'] == 'Environmental']
    soc = [q for q in questions if q['pillar'] == 'Social']
    gov = [q for q in questions if q['pillar'] == 'Governance']
    return env, soc, gov

env_questions, soc_questions, gov_questions = categorize_questions(questions)

industry_weights = {
    "Manufacturing": {"Environmental": 1.5, "Social": 1.0, "Governance": 1.0},
    "IT/Services": {"Environmental": 1.0, "Social": 1.2, "Governance": 1.2},
    "Finance": {"Environmental": 0.8, "Social": 1.0, "Governance": 1.5},
    "Healthcare": {"Environmental": 1.2, "Social": 1.2, "Governance": 1.0},
    "Other": {"Environmental": 1.0, "Social": 1.0, "Governance": 1.0}
}

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
    sector = st.session_state.company_info.get("sector_type", "Other")
    weights = industry_weights.get(sector, {"Environmental": 1.0, "Social": 1.0, "Governance": 1.0})

    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
    total_score = 0

    for q in questions:
        score = q["options"].index(responses[q["id"]])
        weighted_score = score * weights[q["pillar"]]
        total_score += weighted_score
        pillar_scores[q["pillar"]] += weighted_score
        pillar_counts[q["pillar"]] += weights[q["pillar"]]

    # Prevent division by zero if a pillar has no questions
    verde_score = round((total_score / (5 * sum(pillar_counts.values()))) * 100) if sum(pillar_counts.values()) else 0
    return verde_score, pillar_scores, pillar_counts

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Your Agentic ESG Copilot")
    st.caption("Crafted by Hemaang Patkar")
    st.markdown("""VerdeIQ simulates the behavior of a real-world ESG consultant — not just scoring, but analyzing, advising, and adapting.""")
    if st.button("Launch ESG Copilot →"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Agentic Profile Setup")
    with st.form("org_form"):
        c1, c2 = st.columns(2)
        with c1:
            info = st.session_state.company_info
            info['name'] = st.text_input("Company Name", value=info.get('name', ''))
            info['industry'] = st.text_input("Industry", value=info.get('industry', ''))
            info['location'] = st.text_input("City", value=info.get('location', ''))
            info['supply_chain_exposure'] = st.selectbox("Supply Chain Exposure", ["Local", "Regional", "Global"], index=["Local", "Regional", "Global"].index(info.get('supply_chain_exposure', "Local")))
            info['carbon_disclosure'] = st.radio("Discloses Carbon Emissions?", ["Yes", "No"], index=["Yes", "No"].index(info.get('carbon_disclosure', "No")))
            info['third_party_audits'] = st.radio("Undergoes 3rd-Party ESG Audits?", ["Yes", "No", "Planned"], index=["Yes", "No", "Planned"].index(info.get('third_party_audits', "No")))
            info['stakeholder_reporting'] = st.radio("Publishes Stakeholder Reports?", ["Yes", "No"], index=["Yes", "No"].index(info.get('stakeholder_reporting', "No")))
            info['materiality_assessment_status'] = st.radio("Materiality Assessment Conducted?", ["Yes", "No", "In Progress"], index=["Yes", "No", "In Progress"].index(info.get('materiality_assessment_status', "No")))
            info['board_esg_committee'] = st.radio("Board-Level ESG Committee?", ["Yes", "No"], index=["Yes", "No"].index(info.get('board_esg_committee', "No")))
        with c2:
            info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"], index=["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"].index(info.get('size', "1-10")))
            info['esg_goals'] = st.multiselect("Core ESG Intentions", ["Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"], default=info.get('esg_goals', []))
            info['public_status'] = st.radio("Listed Status", ["Yes", "No", "Planning to"], index=["Yes", "No", "Planning to"].index(info.get('public_status', "No")))
            info['sector_type'] = st.radio("Sector Type", list(industry_weights.keys()), index=list(industry_weights.keys()).index(info.get('sector_type', "Other")))
            info['esg_team_size'] = st.selectbox("Dedicated ESG Team Size", ["0", "1-2", "3-5", "6-10", "10+"], index=["0", "1-2", "3-5", "6-10", "10+"].index(info.get('esg_team_size', "0")))
            info['internal_esg_training'] = st.radio("Internal ESG Training Programs?", ["Yes", "No"], index=["Yes", "No"].index(info.get('internal_esg_training', "No")))
            info['climate_risk_policy'] = st.radio("Climate Risk Mitigation Policy?", ["Yes", "No"], index=["Yes", "No"].index(info.get('climate_risk_policy', "No")))
            info['regulatory_exposure'] = st.selectbox("Regulatory Exposure", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(info.get('regulatory_exposure', "Low")))

        info['region'] = st.selectbox("Main Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"], index=["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"].index(info.get('region', "North America")))
        info['years_operating'] = st.slider("Years Since Founding", 0, 200, info.get('years_operating', 5))
        # Ensure date inputs handle default value correctly (e.g., convert string to date if stored as string)
        if 'last_esg_report' in info and isinstance(info['last_esg_report'], str):
            try:
                info['last_esg_report'] = date.fromisoformat(info['last_esg_report'])
            except ValueError:
                info['last_esg_report'] = date.today()
        if 'last_training_date' in info and isinstance(info['last_training_date'], str):
            try:
                info['last_training_date'] = date.fromisoformat(info['last_training_date'])
            except ValueError:
                info['last_training_date'] = date.today()
        info['last_esg_report'] = st.date_input("Last ESG Report Published", value=info.get('last_esg_report', date.today()))
        info['last_training_date'] = st.date_input("Last ESG Training Conducted", value=info.get('last_training_date', date.today()))

        if st.form_submit_button("Activate ESG Analysis →"):
            st.session_state.page = "env"
            st.rerun()

elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.form_submit_button("Continue to Social 🤝"):
            st.session_state.page = "soc"
            st.rerun()

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.form_submit_button("Continue to Governance 🏛️"):
            st.session_state.page = "gov"
            st.rerun()

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.form_submit_button("Review My Answers 🔍"):
            st.session_state.page = "review"
            st.rerun()

elif st.session_state.page == "review":
    st.title("🔍 Final Review")
    st.markdown("Please review your answers before proceeding.")
    for pillar in ["Environmental", "Social", "Governance"]:
        st.subheader(pillar)
        for q in [q for q in questions if q["pillar"] == pillar]:
            # Ensure the key exists before accessing
            if q['id'] in st.session_state.responses:
                st.markdown(f"**{q['id']}**: {st.session_state.responses[q['id']]}")
            else:
                st.markdown(f"**{q['id']}**: Not answered") # Fallback for un-answered questions
    if st.button("Generate My ESG Score ✨"):
        st.session_state.page = "results"
        st.rerun()

elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Agentic ESG Summary")
    verde_score, scores, counts = calculate_scores(st.session_state.responses)
    labels = list(scores.keys())
    values = [scores[k] / counts[k] if counts[k] else 0 for k in labels]

    badge, badge_class = (
        ("🌱 Seedling", "badge-red") if verde_score < 30 else
        ("🌿 Sprout", "badge-yellow") if verde_score < 50 else
        ("🍃 Developing", "badge-yellow") if verde_score < 70 else
        ("🌳 Mature", "badge-green") if verde_score < 90 else
        ("✨ Leader", "badge-green")
    )

    st.metric(label="Your ESG Copilot Score", value=f"{verde_score}/100")
    st.markdown(f"<div class='{badge_class}'>Agentic Tier: {badge}</div>", unsafe_allow_html=True)
    st.caption("VerdeBot interprets your ESG behavior across the three strategic pillars:")

    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Indentation correction for the button and spinner block
    if st.button("🔍 Generate My ESG Analysis & Roadmap (via VerdeBot)"):
        with st.spinner("""
🔍 Initiating Agentic ESG Reasoning...

VerdeBot — your Agentic ESG Copilot — is now:
• Parsing organizational inputs across strategy, disclosure, governance, and operations  
• Aligning responses to global ESG frameworks (GRI, SASB, BRSR, UN SDGs)  
• Inferring maturity signals, compliance posture, and strategic readiness  
• Synthesizing a customized roadmap tuned to your sector, scale, and ESG ambitions  

⏳ This may take **up to a minute** depending on your ESG profile depth.  
"""):
            try:
                info = st.session_state.company_info
                responses = st.session_state.responses
                detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])

                prompt = f"""
You are VerdeBot, an advanced Agentic ESG Copilot and strategic advisor with deep expertise in global sustainability practices, regulatory alignment, and corporate governance. Your role is to act as a senior ESG consultant tasked with translating the following company’s ESG posture into a precise, framework-aligned, and context-aware roadmap.

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
- City: {info.get('location')}
- Supply Chain Exposure: {info.get('supply_chain_exposure')}
- Regulatory Risk: {info.get('regulatory_exposure')}
- Core ESG Intentions: {', '.join(info.get('esg_goals', [])) or 'Not specified'}

📄 **Governance & Policy Indicators**
- Materiality Assessment: {info.get('materiality_assessment_status')}
- ESG Board Committee: {info.get('board_esg_committee')}
- Climate Risk Policy: {info.get('climate_risk_policy')}
- Internal ESG Training: {info.get('internal_esg_training')}
- Carbon Disclosure: {info.get('carbon_disclosure')}
- Third-Party ESG Audits: {info.get('third_party_audits')}
- Stakeholder Reporting: {info.get('stakeholder_reporting')}
- Last ESG Report: {info.get('last_esg_report')}
- Last Training Date: {info.get('last_training_date')}

📊 **Assessment Results**
- VerdeIQ Score: {verde_score}/100
- Tier: {badge}
- Environmental Score: {values[0]:.2f}/5
- Social Score: {values[1]:.2f}/5
- Governance Score: {values[2]:.2f}/5

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
                    # Cohere API might return "text" or "message" in the response depending on version/endpoint
                    roadmap = output.get("text") or output.get("message") or "No roadmap received."

                    st.subheader("📓 VerdeBot's Strategic ESG Roadmap")
                    st.markdown(roadmap)

                    st.download_button(
                        label="⬇️ Download Roadmap as Text",
                        data=roadmap,
                        file_name="VerdeIQ_ESG_Roadmap.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("⚠️ Cohere API key not found in Streamlit secrets.")
            except Exception as e:
                st.error(f"❌ Error generating roadmap: {e}")
