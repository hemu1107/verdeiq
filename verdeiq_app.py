import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
import uuid
import datetime

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Styling & Theming ---
st.markdown("""
    <style>
        .title-style {font-size: 32px; font-weight: bold; color: #228B22;}
        .section-title {font-size: 20px; font-weight: 600; margin-top: 20px;}
        .nav-button {margin: 10px 0;}
    </style>
""", unsafe_allow_html=True)

# --- Load ESG Questions JSON with Industry-Specific Mapping ---
@st.cache_data
def load_questions(sector_type=None):
    file_path = Path("esg_questions.json")
    if not file_path.exists():
        st.error("Questions file not found.")
        st.stop()
    with open(file_path) as f:
        questions = json.load(f)
    
    # Filter or weight questions based on SASB industry classification
    if sector_type:
        sector_mapping = {
            "Manufacturing": ["Extractives & Minerals Processing", "Resource Transformation"],
            "IT/Services": ["Technology & Communications", "Services"],
            "Finance": ["Financials"],
            "Healthcare": ["Health Care"],
            "Other": ["Infrastructure", "Consumer Goods"]
        }
        # Map sector_type to SASB sectors (simplified for demo)
        applicable_sectors = sector_mapping.get(sector_type, ["Infrastructure"])
        filtered_questions = []
        for q in questions:
            # Check if question applies to the sector (based on SASB metadata)
            if not q.get("sasb_sectors") or any(s in applicable_sectors for s in q.get("sasb_sectors", [])):
                # Apply weighting for industry-specific materiality (e.g., emissions higher for Manufacturing)
                if sector_type == "Manufacturing" and "emissions" in q["question"].lower():
                    q["weight"] = q.get("weight", 1) * 1.5  # Higher weight for emissions in Manufacturing
                elif sector_type == "IT/Services" and "emissions" in q["question"].lower():
                    q["weight"] = q.get("weight", 1) * 0.8  # Lower weight for emissions in IT/Services
                else:
                    q["weight"] = q.get("weight", 1)  # Default weight
                filtered_questions.append(q)
        return filtered_questions
    return questions

# --- Split by Pillar ---
def categorize_questions(questions):
    env = [q for q in questions if q['pillar'] == 'Environmental']
    soc = [q for q in questions if q['pillar'] == 'Social']
    gov = [q for q in questions if q['pillar'] == 'Governance']
    return env, soc, gov

# --- Session Management ---
if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.company_info = {}
    st.session_state.review_mode = False
    st.session_state.previous_page = None

# --- Agentic Copilot Introduction ---
def introduce_agent():
    st.info("🤖 Meet VerdeBot: Your ESG Copilot")
    st.caption("VerdeBot will guide you through the ESG assessment journey, adaptively interpreting your inputs to generate strategic insights aligned with global standards like GRI, SASB, and BRSR.")

# --- Helper Functions ---
def show_question_block(q, idx, total):
    st.markdown(f"**{q['id']}: {q['question']}**")
    if q.get('frameworks'):
        st.caption(f"Frameworks: {', '.join(q['frameworks'])} | SASB Sectors: {', '.join(q.get('sasb_sectors', ['All']))}")
    # Add time sensitivity dimension
    if "policy" in q["question"].lower() or "report" in q["question"].lower() or "training" in q["question"].lower():
        st.session_state.responses[f"{q['id']}_last_updated"] = st.date_input(
            f"Last Updated/Reviewed for {q['id']}",
            value=None,
            min_value=datetime.date(2000, 1, 1),
            max_value=datetime.date.today(),
            key=f"{q['id']}_last_updated"
        )
    st.session_state.responses[q['id']] = st.radio(
        label=f"Agentic Analysis {idx + 1} of {total}",
        options=q['options'],
        index=0 if q['id'] not in st.session_state.responses else q['options'].index(st.session_state.responses[q['id']]),
        key=f"{q['id']}_response"
    )
    st.markdown("---")

def calculate_scores(responses, questions):
    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
    total_score = 0
    max_score = 0

    for q in questions:
        if q["id"] in responses:
            score = q["options"].index(responses[q["id"]]) * q.get("weight", 1)
            total_score += score
            max_score += 5 * q.get("weight", 1)  # Max score per question is 5
            pillar_scores[q["pillar"]] += score
            pillar_counts[q["pillar"]] += 1

    verde_score = round((total_score / max_score) * 100) if max_score > 0 else 0
    return verde_score, pillar_scores, pillar_counts

# --- Review Responses Page ---
def show_review_page():
    st.header("📋 Review Your Responses")
    st.caption("Review and edit your responses before final submission.")
    for pillar, q_list in [("Environmental", env_questions), ("Social", soc_questions), ("Governance", gov_questions)]:
        st.subheader(f"{pillar} Responses")
        for q in q_list:
            st.markdown(f"**{q['id']}: {q['question']}**")
            st.write(f"Response: {st.session_state.responses.get(q['id'], 'Not answered')}")
            if f"{q['id']}_last_updated" in st.session_state.responses:
                st.write(f"Last Updated: {st.session_state.responses.get(f'{q['id']}_last_updated', 'Not specified')}")
            st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Edit", key="review_back"):
            st.session_state.page = st.session_state.previous_page
            st.session_state.review_mode = False
            st.rerun()
    with col2:
        if st.button("Submit Responses", key="review_submit"):
            st.session_state.page = "results"
            st.rerun()

# --- Navigation Helper ---
def add_navigation_buttons(current_page, prev_page, next_page, form_id=None):
    col1, col2 = st.columns(2)
    with col1:
        if prev_page and st.button("← Previous", key=f"nav_back_{current_page}", help="Go back to previous section"):
            st.session_state.page = prev_page
            st.rerun()
    with col2:
        if next_page and form_id:
            if st.form_submit_button("Next →", help="Proceed to next section"):
                st.session_state.page = next_page
                st.rerun()
        elif next_page:
            if st.button("Next →", key=f"nav_next_{current_page}", help="Proceed to next section"):
                st.session_state.page = next_page
                st.rerun()

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Your Agentic ESG Copilot")
    st.caption("Crafted by Hemaang Patkar")
    introduce_agent()
    st.markdown("""
    VerdeIQ simulates the behavior of a real-world ESG consultant — not just scoring, but analyzing, advising, and adapting.

    - 🤖 Agentic Persona: VerdeBot interprets your responses
    - 🔎 Industry-aligned prompts mapped to SASB, GRI, BRSR, and UN SDGs
    - 📊 Real-time contextual scoring with time-sensitive insights
    - 🛍️ Roadmaps tailored to your sector, scale, and maturity

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

        add_navigation_buttons("details", None, "env", "org_form")

    # Load questions based on sector type
    questions = load_questions(st.session_state.company_info.get('sector_type'))
    env_questions, soc_questions, gov_questions = categorize_questions(questions)

elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    st.caption("VerdeBot is interpreting your sustainability posture...")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.button("Review Responses", key="env_review"):
            st.session_state.previous_page = "env"
            st.session_state.review_mode = True
            st.session_state.page = "review"
            st.rerun()
        add_navigation_buttons("env", "details", "soc", "env_form")

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    st.caption("Analyzing your team, culture, and external impact...")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.button("Review Responses", key="soc_review"):
            st.session_state.previous_page = "soc"
            st.session_state.review_mode = True
            st.session_state.page = "review"
            st.rerun()
        add_navigation_buttons("soc", "env", "gov", "soc_form")

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    st.caption("Parsing leadership ethics and oversight structures...")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.button("Review Responses", key="gov_review"):
            st.session_state.previous_page = "gov"
            st.session_state.review_mode = True
            st.session_state.page = "review"
            st.rerun()
        add_navigation_buttons("gov", "soc", "results", "gov_form")

elif st.session_state.page == "review":
    show_review_page()

elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Agentic ESG Summary")
    verde_score, scores, counts = calculate_scores(st.session_state.responses, questions)
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
    if st.button("🔍 Generate My ESG Analysis & Roadmap (via VerdeBot)"):
        with st.spinner("""
🔍 Initiating Agentic ESG Reasoning...

VerdeBot — your Agentic ESG Copilot — is now:
• Parsing organizational inputs across strategy, disclosure, governance, and operations  
• Aligning responses to global ESG frameworks (GRI, SASB, BRSR, UN SDGs)  
• Inferring maturity signals, compliance posture, and strategic readiness  
• Synthesizing a customized roadmap tuned to your sector, scale, and ESG ambitions  

⏳ This may take **up to a minute** depending on your ESG profile depth.  
Thank you for your patience as VerdeBot formulates boardroom-ready recommendations!
"""):
            try:
                info = st.session_state.company_info
                responses = st.session_state.responses
                detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" + 
                                             (f" (Last Updated: {responses.get(f'{qid}_last_updated', 'Not specified')})" 
                                              if f"{qid}_last_updated" in responses else "") 
                                             for qid in responses if not qid.endswith("_last_updated")])
                prompt = f"""You are VerdeBot, an advanced Agentic ESG Copilot and strategic advisor with deep expertise in global sustainability practices, regulatory alignment, and corporate governance. Your role is to act as a senior ESG consultant tasked with translating the following company’s ESG posture into a precise, framework-aligned, and context-aware roadmap.

Approach this with the analytical rigor of a McKinsey or BCG ESG lead, blending technical sustainability metrics with industry-specific insights. Ensure your output is:
- Aligned with frameworks such as GRI, SASB, BRSR, and UN SDGs.
- Professional and jargon-savvy — suitable for boardrooms, investors, and compliance officers.
- Specific to inputs — DO NOT hallucinate metrics or add fluffy generalities.
- Incorporates time sensitivity of policies/reports (last updated dates) to assess active ESG practices.
- Tailored to SASB industry-specific materiality (e.g., emissions weighted higher for Manufacturing).

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
   - Identify 3–5 gaps considering disclosures, governance, training, and risk, factoring in time sensitivity (e.g., outdated policies).
   - Reference ESG frameworks like GRI 305, SASB Standards, BRSR Principle 3, SDG 12, etc., with industry-specific materiality (e.g., SASB sector alignment).

2. **Roadmap (0–36 Months)**
   - **Immediate (0–6 months):** Internal capacity-building, audits, dashboards, materiality clarifications.
   - **Mid-Term (6–18 months):** Stakeholder engagement, GRI-aligned reporting, risk-based action plans.
   - **Long-Term (18–36 months):** Third-party disclosures, ESG ratings readiness, governance reform.

3. **Pillar-Wise Breakdown**
   - 2–3 recommendations per pillar, tailored to SASB sector materiality.
   - Tie each point to global ESG frameworks and relevant tools.

4. **Tools & Metrics**
   - Suggest tools, templates, and documents to use immediately (aligned to company maturity and sector).
   - E.g., CDP portal, SASB Materiality Finder, DEI dashboards, ESG risk register.

5. **90-Day Advisory Plan**
   - List 4–5 tactical, confidence-building actions, considering time sensitivity and industry context.

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
