import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Styling & Theming ---
st.markdown("""
    <style>
        .title-style {font-size: 32px; font-weight: bold; color: #228B22;}
        .section-title {font-size: 20px; font-weight: 600; margin-top: 20px;}
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stRadio>label {
            font-weight: bold;
        }
        .stDateInput>label {
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- ESG Questions Data (Simulated JSON with new fields) ---
# In a real application, this would be loaded from a JSON file
# and potentially filtered/weighted based on industry.
# Added 'requires_timestamp' and 'industry_weights' for demonstration.
questions = [
    {
        "id": "E1",
        "pillar": "Environmental",
        "question": "Has your company set specific, measurable targets for reducing greenhouse gas emissions?",
        "options": ["No", "Exploring", "Partial", "Yes, with targets", "Yes, with verified targets"],
        "frameworks": ["GRI 305", "SASB EM-EP-130a.1"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.5, "Cement Manufacturing": 2.0, "IT/Services": 1.0,
            "Finance": 0.8, "Healthcare": 1.0, "Agriculture": 1.8, "Other": 1.0
        }
    },
    {
        "id": "E2",
        "pillar": "Environmental",
        "question": "Does your company have a policy for water management and conservation?",
        "options": ["No", "Informal", "Formal, limited scope", "Formal, comprehensive", "Formal, comprehensive with targets"],
        "frameworks": ["GRI 303", "SASB WR-MM-140a.1"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.2, "Cement Manufacturing": 1.8, "IT/Services": 0.7,
            "Finance": 0.5, "Healthcare": 1.0, "Agriculture": 2.0, "Other": 1.0
        }
    },
    {
        "id": "E3",
        "pillar": "Environmental",
        "question": "How does your company manage waste and hazardous materials?",
        "options": ["No formal process", "Basic recycling", "Waste reduction programs", "Circular economy initiatives", "Zero-waste certified"],
        "frameworks": ["GRI 306", "SASB WM-WM-150a.1"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.3, "Cement Manufacturing": 1.6, "IT/Services": 0.9,
            "Finance": 0.6, "Healthcare": 1.5, "Agriculture": 1.0, "Other": 1.0
        }
    },
    {
        "id": "E4",
        "pillar": "Environmental",
        "question": "Does your company assess and manage biodiversity impacts?",
        "options": ["No", "Informal awareness", "Preliminary assessment", "Formal assessment with mitigation", "Net positive impact initiatives"],
        "frameworks": ["GRI 304", "UN SDG 15"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.2, "IT/Services": 0.5,
            "Finance": 0.7, "Healthcare": 0.8, "Agriculture": 1.8, "Other": 1.0
        }
    },
    {
        "id": "E5",
        "pillar": "Environmental",
        "question": "What is your approach to sustainable sourcing and supply chain management?",
        "options": ["No specific approach", "Basic supplier code of conduct", "Supplier audits for sustainability", "Sustainable sourcing policies", "Certified sustainable supply chain"],
        "frameworks": ["GRI 204", "UN SDG 12"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.5, "Cement Manufacturing": 1.3, "IT/Services": 1.0,
            "Finance": 0.9, "Healthcare": 1.2, "Agriculture": 1.5, "Other": 1.0
        }
    },
    {
        "id": "S1",
        "pillar": "Social",
        "question": "Does your company have a formal policy on diversity, equity, and inclusion (DEI)?",
        "options": ["No", "Informal efforts", "Policy in development", "Formal policy", "Formal policy with measurable targets"],
        "frameworks": ["GRI 405", "UN SDG 5"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.0, "IT/Services": 1.2,
            "Finance": 1.3, "Healthcare": 1.1, "Agriculture": 0.9, "Other": 1.0
        }
    },
    {
        "id": "S2",
        "pillar": "Social",
        "question": "How does your company ensure fair labor practices and human rights in its operations and supply chain?",
        "options": ["No specific measures", "Basic compliance", "Regular audits", "Supplier engagement programs", "Certified fair labor practices"],
        "frameworks": ["GRI 407", "UN SDG 8"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.5, "Cement Manufacturing": 1.2, "IT/Services": 0.8,
            "Finance": 0.9, "Healthcare": 1.0, "Agriculture": 1.5, "Other": 1.0
        }
    },
    {
        "id": "S3",
        "pillar": "Social",
        "question": "What initiatives does your company have for employee health, safety, and well-being?",
        "options": ["Basic compliance", "Wellness programs", "Comprehensive H&S management system", "Proactive well-being initiatives", "Industry leader in H&S"],
        "frameworks": ["GRI 403", "SASB HR-CR-220a.1"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.3, "Cement Manufacturing": 1.4, "IT/Services": 1.0,
            "Finance": 1.0, "Healthcare": 1.2, "Agriculture": 1.2, "Other": 1.0
        }
    },
    {
        "id": "S4",
        "pillar": "Social",
        "question": "How does your company engage with local communities?",
        "options": ["No engagement", "Ad-hoc donations", "Community investment programs", "Strategic partnerships", "Community-led development initiatives"],
        "frameworks": ["GRI 413", "UN SDG 11"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.5, "IT/Services": 0.8,
            "Finance": 0.9, "Healthcare": 1.0, "Agriculture": 1.3, "Other": 1.0
        }
    },
    {
        "id": "S5",
        "pillar": "Social",
        "question": "What is your approach to customer privacy and data security?",
        "options": ["No specific measures", "Basic data protection", "Compliance with regulations", "Robust data security protocols", "Certified data privacy frameworks"],
        "frameworks": ["GRI 418", "SASB FB-SP-230a.1"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 0.8, "Cement Manufacturing": 0.7, "IT/Services": 1.5,
            "Finance": 2.0, "Healthcare": 1.8, "Agriculture": 0.9, "Other": 1.0
        }
    },
    {
        "id": "G1",
        "pillar": "Governance",
        "question": "Is there a documented whistle-blower policy in place and is it regularly communicated?",
        "options": ["No", "Informal", "Formal, not regularly communicated", "Formal and communicated", "Formal, communicated, and protected"],
        "frameworks": ["GRI 205", "BRSR Principle 6"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.0, "IT/Services": 1.0,
            "Finance": 1.2, "Healthcare": 1.0, "Agriculture": 1.0, "Other": 1.0
        }
    },
    {
        "id": "G2",
        "pillar": "Governance",
        "question": "How is ESG oversight integrated into your board of directors' structure?",
        "options": ["No integration", "Ad-hoc discussions", "Board committee with ESG mandate", "Dedicated ESG committee", "Board-level ESG expertise and strategy"],
        "frameworks": ["GRI 102-18", "SASB FN-CR-510a.1"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.0, "IT/Services": 1.1,
            "Finance": 1.3, "Healthcare": 1.0, "Agriculture": 0.9, "Other": 1.0
        }
    },
    {
        "id": "G3",
        "pillar": "Governance",
        "question": "What is your company's policy on anti-corruption and bribery?",
        "options": ["No policy", "Informal guidelines", "Formal policy", "Formal policy with training", "Formal policy, training, and regular audits"],
        "frameworks": ["GRI 205", "BRSR Principle 6"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.2, "Cement Manufacturing": 1.2, "IT/Services": 1.0,
            "Finance": 1.5, "Healthcare": 1.0, "Agriculture": 1.0, "Other": 1.0
        }
    },
    {
        "id": "G4",
        "pillar": "Governance",
        "question": "How does your company manage ethical conduct and business integrity?",
        "options": ["No formal code", "Basic code of conduct", "Comprehensive code with training", "Ethics committee and reporting channels", "Culture of integrity with continuous improvement"],
        "frameworks": ["GRI 205", "BRSR Principle 6"],
        "requires_timestamp": False,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.0, "IT/Services": 1.0,
            "Finance": 1.1, "Healthcare": 1.0, "Agriculture": 1.0, "Other": 1.0
        }
    },
    {
        "id": "G5",
        "pillar": "Governance",
        "question": "Does your company disclose its ESG performance and progress publicly?",
        "options": ["No", "Informal internal reports", "Limited public disclosure", "Comprehensive sustainability report", "Integrated financial and sustainability report"],
        "frameworks": ["GRI 102-54", "BRSR Principle 9"],
        "requires_timestamp": True,
        "industry_weights": {
            "Manufacturing": 1.0, "Cement Manufacturing": 1.0, "IT/Services": 1.0,
            "Finance": 1.2, "Healthcare": 1.0, "Agriculture": 1.0, "Other": 1.0
        }
    }
]


# --- Split by Pillar ---
def categorize_questions(questions_list):
    env = [q for q in questions_list if q['pillar'] == 'Environmental']
    soc = [q for q in questions_list if q['pillar'] == 'Social']
    gov = [q for q in questions_list if q['pillar'] == 'Governance']
    return env, soc, gov

env_questions, soc_questions, gov_questions = categorize_questions(questions)

# --- Session Management ---
if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.timestamps = {} # New: to store date inputs
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

    # Display radio options
    st.session_state.responses[q['id']] = st.radio(
        label=f"Agentic Analysis {idx + 1} of {total}",
        options=q['options'],
        index=q['options'].index(st.session_state.responses.get(q['id'], q['options'][0])), # Retain previous selection
        key=f"{q['id']}_radio" # Unique key for radio button
    )

    # Add timestamp input if required
    if q.get('requires_timestamp'):
        default_date = st.session_state.timestamps.get(q['id'], date.today())
        st.session_state.timestamps[q['id']] = st.date_input(
            f"Last Updated/Reviewed for {q['id']}",
            value=default_date,
            key=f"{q['id']}_date" # Unique key for date input
        )
    st.markdown("---")

def calculate_scores(responses, company_info, all_questions):
    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_max_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    total_score = 0
    total_max_score = 0

    selected_industry = company_info.get('sector_type', 'Other')

    for q in all_questions:
        if q['id'] in responses:
            score_value = q["options"].index(responses[q["id"]])
            # Apply industry-specific weighting
            weight = q["industry_weights"].get(selected_industry, 1.0)
            
            weighted_score = score_value * weight
            max_possible_score_for_q = (len(q["options"]) - 1) * weight # Max score for this question (e.g., 4 * weight)

            total_score += weighted_score
            total_max_score += max_possible_score_for_q

            pillar_scores[q["pillar"]] += weighted_score
            pillar_max_scores[q["pillar"]] += max_possible_score_for_q

    verde_score = round((total_score / total_max_score) * 100) if total_max_score > 0 else 0

    # Calculate average pillar scores out of 5 (or max option value)
    avg_pillar_scores = {
        pillar: (pillar_scores[pillar] / pillar_max_scores[pillar]) * 5 if pillar_max_scores[pillar] > 0 else 0
        for pillar in pillar_scores
    }
    
    return verde_score, avg_pillar_scores

# --- Navigation functions ---
def go_to_page(page_name):
    st.session_state.page = page_name
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
        go_to_page("details")

elif st.session_state.page == "details":
    st.title("🏢 Agentic Profile Setup")
    st.caption("VerdeBot is learning your company DNA...")
    with st.form("org_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.company_info['name'] = st.text_input("Company Name", value=st.session_state.company_info.get('name', ''))
            st.session_state.company_info['industry'] = st.text_input("Industry (e.g., Software, Automotive)", value=st.session_state.company_info.get('industry', ''))
            st.session_state.company_info['location'] = st.text_input("City", value=st.session_state.company_info.get('location', ''))
            st.session_state.company_info['supply_chain_exposure'] = st.selectbox("Supply Chain Exposure", ["Local", "Regional", "Global"], index=["Local", "Regional", "Global"].index(st.session_state.company_info.get('supply_chain_exposure', "Local")))
            st.session_state.company_info['carbon_disclosure'] = st.radio("Discloses Carbon Emissions?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.company_info.get('carbon_disclosure', "No")))
            st.session_state.company_info['third_party_audits'] = st.radio("Undergoes 3rd-Party ESG Audits?", ["Yes", "No", "Planned"], index=["Yes", "No", "Planned"].index(st.session_state.company_info.get('third_party_audits', "No")))
            st.session_state.company_info['stakeholder_reporting'] = st.radio("Publishes Stakeholder Reports?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.company_info.get('stakeholder_reporting', "No")))
            st.session_state.company_info['materiality_assessment_status'] = st.radio("Materiality Assessment Conducted?", ["Yes", "No", "In Progress"], index=["Yes", "No", "In Progress"].index(st.session_state.company_info.get('materiality_assessment_status', "No")))
            st.session_state.company_info['board_esg_committee'] = st.radio("Board-Level ESG Committee?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.company_info.get('board_esg_committee', "No")))
        with c2:
            st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"], index=["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"].index(st.session_state.company_info.get('size', "1-10")))
            st.session_state.company_info['esg_goals'] = st.multiselect("Core ESG Intentions", [
                "Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"], default=st.session_state.company_info.get('esg_goals', []))
            st.session_state.company_info['public_status'] = st.radio("Listed Status", ["Yes", "No", "Planning to"], index=["Yes", "No", "Planning to"].index(st.session_state.company_info.get('public_status', "No")))
            # More granular sector types for industry-specific calibration
            st.session_state.company_info['sector_type'] = st.radio("Sector Type (for industry-specific weighting)", [
                "Manufacturing", "IT/Services", "Finance", "Healthcare", "Agriculture", "Cement Manufacturing", "Other"
            ], index=[
                "Manufacturing", "IT/Services", "Finance", "Healthcare", "Agriculture", "Cement Manufacturing", "Other"
            ].index(st.session_state.company_info.get('sector_type', "Other")))
            st.session_state.company_info['esg_team_size'] = st.selectbox("Dedicated ESG Team Size", ["0", "1-2", "3-5", "6-10", "10+"], index=["0", "1-2", "3-5", "6-10", "10+"].index(st.session_state.company_info.get('esg_team_size', "0")))
            st.session_state.company_info['internal_esg_training'] = st.radio("Internal ESG Training Programs?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.company_info.get('internal_esg_training', "No")))
            st.session_state.company_info['climate_risk_policy'] = st.radio("Climate Risk Mitigation Policy?", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.company_info.get('climate_risk_policy', "No")))
            st.session_state.company_info['regulatory_exposure'] = st.selectbox("Regulatory Exposure", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(st.session_state.company_info.get('regulatory_exposure', "Low")))

        st.session_state.company_info['region'] = st.selectbox("Main Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"], index=["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"].index(st.session_state.company_info.get('region', "North America")))
        st.session_state.company_info['years_operating'] = st.slider("Years Since Founding", 0, 200, st.session_state.company_info.get('years_operating', 5))

        if st.form_submit_button("Activate ESG Analysis →"):
            go_to_page("env")

elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    st.caption("VerdeBot is interpreting your sustainability posture...")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Back to Profile Setup"):
                go_to_page("details")
        with col2:
            if st.form_submit_button("Continue to Social 🤝"):
                go_to_page("soc")

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    st.caption("Analyzing your team, culture, and external impact...")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Back to Environmental 🌿"):
                go_to_page("env")
        with col2:
            if st.form_submit_button("Continue to Governance 🏛️"):
                go_to_page("gov")

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    st.caption("Parsing leadership ethics and oversight structures...")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Back to Social 🤝"):
                go_to_page("soc")
        with col2:
            if st.form_submit_button("Review All Responses ✨"):
                go_to_page("review")

elif st.session_state.page == "review":
    st.title("📋 Review Your ESG Assessment")
    st.caption("Please review your responses before generating the final ESG analysis. You can go back to edit any section.")

    st.subheader("🏢 Company Profile")
    for key, value in st.session_state.company_info.items():
        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    st.markdown("---")

    st.subheader("🌿 Environmental Responses")
    for q in env_questions:
        response = st.session_state.responses.get(q['id'], "No response")
        timestamp = st.session_state.timestamps.get(q['id'])
        st.write(f"**{q['id']}: {q['question']}**")
        st.write(f"Response: {response}")
        if q.get('requires_timestamp') and timestamp:
            st.write(f"Last Updated/Reviewed: {timestamp.strftime('%Y-%m-%d')}")
        st.markdown("---")

    st.subheader("🤝 Social Responses")
    for q in soc_questions:
        response = st.session_state.responses.get(q['id'], "No response")
        timestamp = st.session_state.timestamps.get(q['id'])
        st.write(f"**{q['id']}: {q['question']}**")
        st.write(f"Response: {response}")
        if q.get('requires_timestamp') and timestamp:
            st.write(f"Last Updated/Reviewed: {timestamp.strftime('%Y-%m-%d')}")
        st.markdown("---")

    st.subheader("🏛️ Governance Responses")
    for q in gov_questions:
        response = st.session_state.responses.get(q['id'], "No response")
        timestamp = st.session_state.timestamps.get(q['id'])
        st.write(f"**{q['id']}: {q['question']}**")
        st.write(f"Response: {response}")
        if q.get('requires_timestamp') and timestamp:
            st.write(f"Last Updated/Reviewed: {timestamp.strftime('%Y-%m-%d')}")
        st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Go Back to Edit (Governance)"):
            go_to_page("gov")
    with col2:
        if st.button("Generate Agentic Summary ✨"):
            go_to_page("results")


elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Agentic ESG Summary")
    verde_score, avg_pillar_scores = calculate_scores(st.session_state.responses, st.session_state.company_info, questions)
    
    labels = list(avg_pillar_scores.keys())
    values = [avg_pillar_scores[k] for k in labels]

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
                timestamps = st.session_state.timestamps

                detailed_answers = []
                for q in questions:
                    response_text = responses.get(q['id'], "Not answered")
                    timestamp_text = ""
                    if q.get('requires_timestamp') and q['id'] in timestamps:
                        timestamp_text = f" (Last Updated: {timestamps[q['id']].strftime('%Y-%m-%d')})"
                    detailed_answers.append(f"- {q['id']}: {response_text}{timestamp_text}")
                detailed_answers_str = "\n".join(detailed_answers)

                prompt = f"""You are VerdeBot, an advanced Agentic ESG Copilot and strategic advisor with deep expertise in global sustainability practices, regulatory alignment, and corporate governance. Your role is to act as a senior ESG consultant tasked with translating the following company’s ESG posture into a precise, framework-aligned, and context-aware roadmap.

Approach this with the analytical rigor of a McKinsey or BCG ESG lead, blending technical sustainability metrics with industry-specific insights. Ensure your output is:
- Aligned with frameworks such as GRI, SASB, BRSR, and UN SDGs.
- Professional and jargon-savvy — suitable for boardrooms, investors, and compliance officers.
- Specific to inputs — DO NOT hallucinate metrics or add fluffy generalities.

---

🏢 **Company Profile**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Sector Type: {info.get('sector_type')} (Industry-specific weighting applied in scoring)
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
- Environmental Maturity: {avg_pillar_scores.get('Environmental', 0):.2f}/5
- Social Maturity: {avg_pillar_scores.get('Social', 0):.2f}/5
- Governance Maturity: {avg_pillar_scores.get('Governance', 0):.2f}/5

🧠 **Self-Assessment Snapshot (including Last Updated/Reviewed dates)**
{detailed_answers_str}

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

                # Reverted to Cohere API as per user's original request
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
    
    if st.button("Start New Assessment"):
        # Reset session state for a new assessment
        st.session_state.page = "intro"
        st.session_state.responses = {}
        st.session_state.timestamps = {}
        st.session_state.company_info = {}
        st.rerun()
