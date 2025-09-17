# --- Enhanced VerdeIQ ESG Assessment App with Agentic AI Persona and Refined UI/UX ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from datetime import date # Import date for handling date inputs

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Define the logo URL ---
# This URL is directly used by st.image to fetch the logo from the web.
LOGO_URL = "https://static.wixstatic.com/media/dc163e_321b2631dcf34be580eeff92e8a5fe33~mv2.png/v1/fill/w_608,h_608,al_c,q_90,usm_0.66_1.00_0.01,enc_avif,quality_auto/dc163e_321b2631dcf34be580eeff92e8a5fe33~mv2.png"

# --- Styling & Theming ---
st.markdown("""
    <style>
        .title-style {font-size: 38px; font-weight: bold; color: #1E8449; text-align: center; margin-bottom: 25px;}
        .section-title {font-size: 24px; font-weight: 600; margin-top: 30px; color: #2C3E50;}
        .stButton>button {
            background-color: #28B463;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #239B56;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .stRadio div[role="radiogroup"] label {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 5px;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
            transition: all 0.15s ease-in-out;
            cursor: pointer; /* Indicate clickable */
        }
        .stRadio div[role="radiogroup"] label:hover {
            background-color: #eee;
        }
        /* Style for selected radio button - Streamlit uses a specific class */
        .stRadio div[role="radiogroup"] label.st-dg { 
            background-color: #D4EDDA !important;
            border-color: #28a745 !important;
            color: #1a5e2a !important; /* Darker text for selected */
        }
        .feedback-box {
            background-color: #E6F3F0;
            border-left: 5px solid #28B463;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            font-style: italic;
            color: #2C3E50;
        }
        /* Badge styling for score tiers */
        .badge-red {color: #E74C3C; font-weight: bold; background-color: #FADBD8; padding: 5px 10px; border-radius: 5px; display: inline-block;}
        .badge-yellow {color: #F39C12; font-weight: bold; background-color: #FCF3CF; padding: 5px 10px; border-radius: 5px; display: inline-block;}
        .badge-green {color: #28B463; font-weight: bold; background-color: #D4EDDA; padding: 5px 10px; border-radius: 5px; display: inline-block;}
        .stAlert { margin-bottom: 20px; }
        
        /* Table styling for maturity tiers */
        .maturity-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .maturity-table th, .maturity-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .maturity-table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- Load ESG Questions JSON ---
# This function is cached to prevent reloading the JSON on every rerun.
@st.cache_data
def load_questions():
    """
    Loads ESG questions from a JSON file.
    Caches the data to avoid re-loading on every Streamlit rerun.
    """
    file_path = Path("esg_questions.json")
    if not file_path.exists():
        st.error("Error: 'esg_questions.json' file not found. Please ensure it's in the same directory.")
        st.stop() # Halts the app execution if the file is missing.
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

questions = load_questions()

# --- Split by Pillar ---
def categorize_questions(questions_list):
    """Categorizes questions into Environmental, Social, and Governance pillars."""
    env = [q for q in questions_list if q['pillar'] == 'Environmental']
    soc = [q for q in questions_list if q['pillar'] == 'Social']
    gov = [q for q in questions_list if q['pillar'] == 'Governance']
    return env, soc, gov

env_questions, soc_questions, gov_questions = categorize_questions(questions)

# --- Industry Weights for Scoring (Agentic Adaptation) ---
# VerdeBot adjusts score weights based on industry relevance to provide context-aware insights.
industry_weights = {
    "Manufacturing": {"Environmental": 1.5, "Social": 1.0, "Governance": 1.0},
    "IT/Services": {"Environmental": 1.0, "Social": 1.2, "Governance": 1.2},
    "Finance": {"Environmental": 0.8, "Social": 1.0, "Governance": 1.5},
    "Healthcare": {"Environmental": 1.2, "Social": 1.2, "Governance": 1.0},
    "Other": {"Environmental": 1.0, "Social": 1.0, "Governance": 1.0}
}

# --- Session Management ---
# Initialize session state variables if they don't exist.
if "page" not in st.session_state:
    st.session_state.page = "intro"
    st.session_state.responses = {}
    st.session_state.company_info = {}
    st.session_state.current_page_index = 0 # For progress bar
    st.session_state.results_generated = False # New state to lock navigation

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

# Update current page index for progress bar
st.session_state.current_page_index = pages.index(st.session_state.page)
total_pages = len(pages)
progress_percentage = (st.session_state.current_page_index / (total_pages - 1)) * 100 if total_pages > 1 else 0

with st.sidebar:
    # --- LOGO INTEGRATION IN SIDEBAR using URL ---
    # Adjusted width for sidebar to fit nicely.
    st.image(LOGO_URL, width=120) # Slightly smaller width for sidebar
    st.markdown("---") # Separator below the logo

    st.markdown("## 🧭 Navigation")
    st.progress(progress_percentage / 100, text=f"Progress: {int(progress_percentage)}%")
    st.markdown("---")
    for i, p in enumerate(pages):
        # Modified navigation logic: If results are generated, disable all navigation except the current page.
        is_disabled = (st.session_state.results_generated and p != st.session_state.page) or \
                      (i > st.session_state.current_page_index and not st.session_state.results_generated)
        
        if p == st.session_state.page:
            st.markdown(f"**➤ {titles[p]}**")
        else:
            if st.button(titles[p], key=f"sidebar_btn_{p}", disabled=is_disabled):
                st.session_state.page = p
                st.rerun()
    st.markdown("---")
    
# --- Helper Functions ---
def show_question_block(q, idx, total):
    """Displays a single ESG question with its options and captures the user's response."""
    st.markdown(f"**{q['id']}: {q['question']}**")
    if q.get('frameworks'):
        st.caption(f"**Framework Alignment:** {', '.join(q['frameworks'])} _(VerdeBot considers these for detailed analysis)_")
    
    # Pre-select the existing response if available
    current_response_index = 0
    if q['id'] in st.session_state.responses and st.session_state.responses[q['id']] in q['options']:
        try:
            current_response_index = q['options'].index(st.session_state.responses[q['id']])
        except ValueError:
            current_response_index = 0

    st.session_state.responses[q['id']] = st.radio(
        label=f"Your Current Stance ({idx + 1} of {total})",
        options=q['options'],
        index=current_response_index,
        key=f"{q['id']}_radio" # Unique key for each radio button
    )
    st.markdown("---")

def calculate_scores(responses):
    """
    Calculates the overall VerdeIQ score and pillar-wise scores.
    VerdeBot uses industry weights to provide a context-aware score.
    """
    sector = st.session_state.company_info.get("sector_type", "Other")
    weights = industry_weights.get(sector, {"Environmental": 1.0, "Social": 1.0, "Governance": 1.0})

    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_weighted_counts = {"Environmental": 0, "Social": 0, "Governance": 0} # Track sum of weights for normalization
    total_weighted_score = 0
    total_possible_weighted_score = 0 # To calculate accurate overall percentage

    for q in questions:
        if q["id"] in responses and responses[q["id"]] in q["options"]: # Only consider answered questions with valid options
            score = q["options"].index(responses[q["id"]]) # 0 for first option, 1 for second, etc. (assuming 0-4 scale)
            max_option_score = len(q["options"]) - 1 

            weighted_score = score * weights.get(q["pillar"], 1.0) # Use .get with default 1.0 for safety
            total_weighted_score += weighted_score
            
            pillar_scores[q["pillar"]] += weighted_score
            pillar_weighted_counts[q["pillar"]] += weights.get(q["pillar"], 1.0)
            total_possible_weighted_score += max_option_score * weights.get(q["pillar"], 1.0)

    verde_score = 0
    if total_possible_weighted_score > 0:
        verde_score = round((total_weighted_score / total_possible_weighted_score) * 100)
    
    # Calculate average score per pillar, normalized to a 0-5 scale (max score per question)
    normalized_pillar_values = {
        pillar: (score / count) if count > 0 else 0
        for pillar, score, count in zip(pillar_scores.keys(), pillar_scores.values(), pillar_weighted_counts.values())
    }

    return verde_score, normalized_pillar_values, pillar_weighted_counts

# --- Pages ---
if st.session_state.page == "intro":
    # --- LOGO INTEGRATION ON INTRO PAGE using URL ---
    # Removed the image from the intro page as requested.
    
    st.markdown("<div class='title-style'>Welcome to VerdeIQ!</div>", unsafe_allow_html=True)
    st.subheader("Your Agentic ESG Copilot")
    st.caption("Crafted by Hemaang Patkar")
    
    st.info("💡 **Expected time to complete the assessment: ~10-15 minutes.**") # Estimated time
    
    st.markdown("""
    **VerdeIQ** simulates the behavior of a real-world ESG consultant. It doesn't just score; it **analyzes**, **advises**, and **adapts** based on your company's unique profile.

    Here’s what makes VerdeIQ truly agentic:
    * 🤖 **Agentic Persona (VerdeBot):** Our AI interprets your inputs, understanding nuances to provide relevant insights.
    * 🔎 **Framework Alignment:** Your responses are mapped against global ESG frameworks like GRI, SASB, BRSR, and UN SDGs, ensuring robust and credible analysis.
    * 📊 **Contextual Scoring & Advisory:** VerdeBot adapts its scoring weights based on your industry and company details, providing truly personalized recommendations.
    * 🛣️ **Tailored Roadmaps:** Receive actionable roadmaps curated specifically for your company’s size, maturity, and sector.
    """)
    st.markdown("---")

    st.markdown("<h3 class='section-title'>📊 Maturity Tiers: Where does your company stand?</h3>", unsafe_allow_html=True)
    st.markdown("""
    VerdeIQ categorizes your ESG maturity into distinct tiers, guiding your journey towards sustainability leadership:
    * **🌱 Seedling (0–29):** Early stages, foundational efforts recommended.
    * **🌿 Sprout (30–49):** Growing awareness, initial steps toward integration.
    * **🍃 Developing (50–69):** Established practices, room for strategic enhancements.
    * **🌳 Mature (70–89):** Robust ESG programs, ready for advanced reporting.
    * **✨ Leader (90–100):** Exemplary performance, setting industry benchmarks.
    """)
    st.markdown("---")

    if st.button("Launch ESG Copilot →"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Agentic Profile Setup")
    st.caption("VerdeBot is learning your company's DNA to provide the most relevant analysis. The more detail, the smarter your copilot becomes!")
    
    with st.form("org_form"):
        info = st.session_state.company_info # Reference the session state dictionary directly

        c1, c2 = st.columns(2)
        with c1:
            info['name'] = st.text_input("Company Name", value=info.get('name', ''))
            info['industry'] = st.text_input("Industry", value=info.get('industry', ''))
            info['location'] = st.text_input("City", value=info.get('location', ''))
            
            supply_chain_options = ["Local", "Regional", "Global"]
            info['supply_chain_exposure'] = st.selectbox(
                "Supply Chain Exposure", 
                supply_chain_options, 
                index=supply_chain_options.index(info.get('supply_chain_exposure', "Local"))
            )
            
            carbon_disclosure_options = ["Yes", "No"]
            info['carbon_disclosure'] = st.radio(
                "Discloses Carbon Emissions?", 
                carbon_disclosure_options, 
                index=carbon_disclosure_options.index(info.get('carbon_disclosure', "No"))
            )
            
            third_party_options = ["Yes", "No", "Planned"]
            info['third_party_audits'] = st.radio(
                "Undergoes 3rd-Party ESG Audits?", 
                third_party_options, 
                index=third_party_options.index(info.get('third_party_audits', "No"))
            )
            
            stakeholder_options = ["Yes", "No"]
            info['stakeholder_reporting'] = st.radio(
                "Publishes Stakeholder Reports?", 
                stakeholder_options, 
                index=stakeholder_options.index(info.get('stakeholder_reporting', "No"))
            )
            
            materiality_options = ["Yes", "No", "In Progress"]
            info['materiality_assessment_status'] = st.radio(
                "Materiality Assessment Conducted?", 
                materiality_options, 
                index=materiality_options.index(info.get('materiality_assessment_status', "No"))
            )
            
            board_esg_options = ["Yes", "No"]
            info['board_esg_committee'] = st.radio(
                "Board-Level ESG Committee?", 
                board_esg_options, 
                index=board_esg_options.index(info.get('board_esg_committee', "No"))
            )
        with c2:
            team_size_options = ["1-10", "11-50", "51-200", "201-500", "500-1000", "1000+"]
            info['size'] = st.selectbox(
                "Team Size", 
                team_size_options, 
                index=team_size_options.index(info.get('size', "1-10"))
            )
            
            esg_goals_options = ["Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"]
            info['esg_goals'] = st.multiselect(
                "Core ESG Intentions", 
                esg_goals_options, 
                default=info.get('esg_goals', [])
            )
            
            public_status_options = ["Yes", "No", "Planning to"]
            info['public_status'] = st.radio(
                "Listed Status", 
                public_status_options, 
                index=public_status_options.index(info.get('public_status', "No"))
            )
            
            sector_type_options = list(industry_weights.keys())
            info['sector_type'] = st.radio(
                "Sector Type", 
                sector_type_options, 
                index=sector_type_options.index(info.get('sector_type', "Other"))
            )
            
            esg_team_size_options = ["0", "1-2", "3-5", "6-10", "10+"]
            info['esg_team_size'] = st.selectbox(
                "Dedicated ESG Team Size", 
                esg_team_size_options, 
                index=esg_team_size_options.index(info.get('esg_team_size', "0"))
            )
            
            internal_training_options = ["Yes", "No"]
            info['internal_esg_training'] = st.radio(
                "Internal ESG Training Programs?", 
                internal_training_options, 
                index=internal_training_options.index(info.get('internal_esg_training', "No"))
            )
            
            climate_risk_options = ["Yes", "No"]
            info['climate_risk_policy'] = st.radio(
                "Climate Risk Mitigation Policy?", 
                climate_risk_options, 
                index=climate_risk_options.index(info.get('climate_risk_policy', "No"))
            )
            
            regulatory_exposure_options = ["Low", "Moderate", "High"]
            info['regulatory_exposure'] = st.selectbox(
                "Regulatory Exposure", 
                regulatory_exposure_options, 
                index=regulatory_exposure_options.index(info.get('regulatory_exposure', "Low"))
            )

        region_options = ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"]
        info['region'] = st.selectbox(
            "Main Operational Region", 
            region_options, 
            index=region_options.index(info.get('region', "North America"))
        )
        
        info['years_operating'] = st.slider("Years Since Founding", 0, 200, info.get('years_operating', 5))
        
        # Handle date inputs, ensuring they are `date` objects for value
        current_esg_report_date = info.get('last_esg_report', date.today())
        if isinstance(current_esg_report_date, str):
            try: current_esg_report_date = date.fromisoformat(current_esg_report_date)
            except ValueError: current_esg_report_date = date.today()
        info['last_esg_report'] = st.date_input("Last ESG Report Published", value=current_esg_report_date, key="last_esg_report_date")

        current_training_date = info.get('last_training_date', date.today())
        if isinstance(current_training_date, str):
            try: current_training_date = date.fromisoformat(current_training_date)
            except ValueError: current_training_date = date.today()
        info['last_training_date'] = st.date_input("Last ESG Training Conducted", value=current_training_date, key="last_training_date")


        st.markdown("---")
        if st.form_submit_button("Activate ESG Analysis →"):
            st.session_state.page = "env"
            st.rerun()
    st.info("💡 Profiling enables VerdeBot to deliver personalized, actionable roadmaps.")

elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    st.caption("VerdeBot is interpreting your sustainability posture regarding your operational impact, resource management, and climate initiatives. Your answers here will inform environmental risk and opportunity assessments.")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        st.markdown("---")
        if st.form_submit_button("Continue to Social 🤝"):
            st.session_state.page = "soc"
            st.rerun()
    st.info("💡 Consistent questions streamline input and power deep analysis.")

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    st.caption("VerdeBot is analyzing your commitments to human capital, community engagement, and product responsibility. These insights will shape recommendations for social equity and stakeholder relations.")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        st.markdown("---")
        if st.form_submit_button("Continue to Governance 🏛️"):
            st.session_state.page = "gov"
            st.rerun()
    st.info("💡 Multi-page flow ensures clean, fatigue-free data collection.")

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    st.caption("VerdeBot is parsing leadership ethics, board oversight, transparency, and compliance structures. This is crucial for evaluating long-term resilience and accountability.")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        st.markdown("---")
        if st.form_submit_button("Review My Answers 🔍"): # Button to go to review page
            st.session_state.page = "review"
            st.rerun()
    st.info("💡 Each pillar adds to a complete, strategy-ready ESG view.")

elif st.session_state.page == "review":
    st.title("🔍 Final Review: Confirm Your Inputs")
    st.caption("VerdeBot is almost ready! Please take a moment to review your provided information. Accuracy here ensures the highest quality ESG analysis.")
    st.markdown("---")

    st.markdown("<h3 class='section-title'>✔️ Your Self-Assessment Responses</h3>", unsafe_allow_html=True)
    for pillar in ["Environmental", "Social", "Governance"]:
        st.subheader(f"Pillar: {pillar}")
        for q_item in [q_data for q_data in questions if q_data["pillar"] == pillar]:
            st.markdown(f"**{q_item['id']}: {q_item['question']}**")
            if q_item['id'] in st.session_state.responses:
                st.write(f"   **Your Answer:** {st.session_state.responses[q_item['id']]}")
            else:
                st.write(f"   **Your Answer:** _Not answered_") # Fallback for unanswered questions
        st.markdown("---")

    if st.button("Generate My ESG Score & Roadmap ✨"):
        st.session_state.page = "results"
        st.session_state.results_generated = True # Set the flag to true
        st.rerun()
    st.info("💡 Reviewing ensures accurate input and trusted AI output.")

elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Agentic ESG Summary")
    st.caption("VerdeBot has completed its analysis. Here’s your comprehensive ESG overview and strategic roadmap.")
    st.markdown("---")

    verde_score, normalized_pillar_values, pillar_weighted_counts = calculate_scores(st.session_state.responses)
    labels = list(normalized_pillar_values.keys())
    values = list(normalized_pillar_values.values())

    # Dynamic badge styling based on score
    badge, badge_class = (
        ("🌱 Seedling", "badge-red") if verde_score < 30 else
        ("🌿 Sprout", "badge-yellow") if verde_score < 50 else
        ("🍃 Developing", "badge-yellow") if verde_score < 70 else
        ("🌳 Mature", "badge-green") if verde_score < 90 else
        ("✨ Leader", "badge-green")
    )

    st.markdown("<h3 class='section-title'>Overall VerdeIQ ESG Score</h3>", unsafe_allow_html=True)
    col_score, col_badge = st.columns([1, 2])
    with col_score:
        st.metric(label="Your ESG Copilot Score", value=f"{verde_score}/100")
    with col_badge:
        st.markdown(f"<div class='{badge_class}'>Agentic Tier: {badge}</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="feedback-box">
        🤖 VerdeBot's Initial Interpretation: Your score of {verde_score}/100 places your company in the {badge} tier. This score reflects VerdeBot's initial assessment of your current ESG maturity based on your self-reported data and industry context.
        <br><br>
        Your ESG Copilot is now ready to interpret your ESG behavior across the three strategic pillars, providing a deeper understanding of your strengths and areas for improvement.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<h3 class='section-title'>Pillar-Wise Performance Radar</h3>", unsafe_allow_html=True)
    st.caption("This radar chart visually represents your company's maturity across Environmental, Social, and Governance pillars, normalized to a 0-5 scale. A larger area indicates stronger performance.")
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        hovertemplate="<b>%{theta}</b>: %{r:.2f}/5<extra></extra>"
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5], # Normalized range from 0 to 5
                dtick=1 # Tick marks every 1 unit
            )
        ),
        showlegend=False,
        height=400 # Adjust chart height
    )
    st.plotly_chart(fig, use_container_width=True) # Changed to use_container_width
    
    st.markdown("---")
    
    # --- Display all Maturity Tiers ---
    st.markdown("<h3 class='section-title'>Understanding All ESG Maturity Tiers</h3>", unsafe_allow_html=True)
    st.markdown("""
    To help you benchmark and plan your growth, here are all the ESG maturity tiers:
    """)
    st.markdown("""
    <table class="maturity-table">
        <thead>
            <tr>
                <th>Tier</th>
                <th>Score Range</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>🌱 Seedling</td>
                <td>0–29</td>
                <td>Early stages, foundational efforts recommended.</td>
            </tr>
            <tr>
                <td>🌿 Sprout</td>
                <td>30–49</td>
                <td>Growing awareness, initial steps toward integration.</td>
            </tr>
            <tr>
                <td>🍃 Developing</td>
                <td>50–69</td>
                <td>Established practices, room for strategic enhancements.</td>
            </tr>
            <tr>
                <td>🌳 Mature</td>
                <td>70–89</td>
                <td>Robust ESG programs, ready for advanced reporting.</td>
            </tr>
            <tr>
                <td>✨ Leader</td>
                <td>90–100</td>
                <td>Exemplary performance, setting industry benchmarks.</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # --- Agentic Recommendation Generator ---
    st.markdown("<h3 class='section-title'>Generate Your Agentic ESG Roadmap</h3>", unsafe_allow_html=True)
    st.markdown("""
    Ready for VerdeBot's deeper dive? Click below to leverage its full agentic capabilities.
    VerdeBot will now synthesize a comprehensive ESG Analysis & Roadmap, tailored specifically for your organization.
    This goes beyond simple scores, offering actionable steps, framework alignments, and strategic advice.
    """)
    if st.button("🔍 Generate My ESG Analysis & Roadmap (via VerdeBot)"):
        with st.spinner("""
🔍 Initiating Agentic ESG Reasoning...

**VerdeBot** — your intelligent ESG Copilot — is now hard at work:
* **Parsing Organizational Inputs:** Analyzing your company profile, self-assessment responses, and implied maturity across strategy, disclosure, governance, and operations.
* **Aligning with Global ESG Frameworks:** Cross-referencing your data with leading frameworks (GRI, SASB, BRSR, UN SDGs) to ensure globally recognized relevance.
* **Inferring Maturity Signals:** Detecting subtle cues in your responses to gauge your current ESG maturity, compliance posture, and strategic readiness.
* **Synthesizing Customized Roadmap:** Crafting a step-by-step, actionable roadmap uniquely tuned to your sector, scale, and specific ESG ambitions.

⏳ This intricate analysis may take **up to a minute** depending on the depth of your ESG profile.
Thank you for your patience as VerdeBot formulates boardroom-ready recommendations!
"""):
            try:
                info = st.session_state.company_info
                responses = st.session_state.responses
                
                # Format detailed answers for the prompt
                detailed_answers = ""
                for q_item in questions:
                    if q_item['id'] in responses:
                        detailed_answers += f"- {q_item['id']}: {q_item['question']} -> {responses[q_item['id']]}\n" 
                    else:
                        detailed_answers += f"- {q_item['id']}: {q_item['question']} -> Not answered\n"


                # Construct the prompt for the LLM
                prompt = f"""
You are VerdeBot, an advanced Agentic ESG Copilot and strategic advisor with deep expertise in global sustainability practices, regulatory alignment, and corporate governance. Your role is to act as a senior ESG consultant tasked with translating the following company’s ESG posture into a precise, framework-aligned, and context-aware roadmap.

Approach this with the analytical rigor of a McKinsey or BCG ESG lead, blending technical sustainability metrics with industry-specific insights. Ensure your output is:
- Aligned with frameworks such as GRI, SASB, BRSR, and UN SDGs.
- Professional and jargon-savvy — suitable for boardrooms, investors, and compliance officers.
- Specific to inputs — DO NOT hallucinate metrics or add fluffy generalities.
- Structured precisely as requested in the sections below.

---

🏢 **Company Profile**
- Name: {info.get('name', 'N/A')}
- Industry: {info.get('industry', 'N/A')}
- Sector Type: {info.get('sector_type', 'N/A')}
- Team Size: {info.get('size', 'N/A')}
- Dedicated ESG Team Size: {info.get('esg_team_size', 'N/A')}
- Public Status: {info.get('public_status', 'N/A')}
- Main Operational Region: {info.get('region', 'N/A')}
- Years in Operation: {info.get('years_operating', 'N/A')}
- Main City: {info.get('location', 'N/A')}
- Supply Chain Exposure: {info.get('supply_chain_exposure', 'N/A')}
- Regulatory Risk Level: {info.get('regulatory_exposure', 'N/A')}
- Core ESG Intentions: {', '.join(info.get('esg_goals', [])) or 'Not specified'}

📄 **Governance & Policy Indicators**
- Materiality Assessment Status: {info.get('materiality_assessment_status', 'N/A')}
- Board-Level ESG Committee: {info.get('board_esg_committee', 'N/A')}
- Climate Risk Mitigation Policy: {info.get('climate_risk_policy', 'N/A')}
- Internal ESG Training Programs: {info.get('internal_esg_training', 'N/A')}
- Carbon Emissions Disclosure: {info.get('carbon_disclosure', 'N/A')}
- Third-Party ESG Audits: {info.get('third_party_audits', 'N/A')}
- Stakeholder Reporting: {info.get('stakeholder_reporting', 'N/A')}
- Last ESG Report Published: {info.get('last_esg_report', 'N/A')}
- Last ESG Training Conducted: {info.get('last_training_date', 'N/A')}

📊 **VerdeIQ Assessment Results**
- Overall VerdeIQ Score: {verde_score}/100
- Agentic Tier: {badge}
- Environmental Maturity Score: {normalized_pillar_values.get('Environmental', 0):.2f}/5
- Social Maturity Score: {normalized_pillar_values.get('Social', 0):.2f}/5
- Governance Maturity Score: {normalized_pillar_values.get('Governance', 0):.2f}/5

🧠 **Detailed Self-Assessment Snapshot**
{detailed_answers}

---

🎯 **Your Task as VerdeBot: Deliver a Structured ESG Advisory Report.**

**1. ESG Profile Summary**
   - Provide a concise executive summary of the company's current ESG posture.
   - Highlight 2-3 key **strengths** across the pillars, linking them to specific company profile fields or strong self-assessment responses.
   - Identify 3-5 critical **gaps or areas for improvement**, considering missing disclosures, governance structures, training, and potential risks.
   - Explicitly reference relevant **ESG frameworks** (e.g., GRI Standards [like GRI 305 for emissions, GRI 401 for employment], SASB Standards [mention a sector-specific one if relevant], BRSR Principles [e.g., Principle 3 for environmental, Principle 5 for employee wellbeing], UN SDGs [e.g., SDG 12 Responsible Consumption and Production, SDG 8 Decent Work and Economic Growth]).

**2. Strategic ESG Roadmap (0–36 Months)**
   - **Immediate (0–6 months):** Focus on foundational, high-impact actions. Include internal capacity-building, initial data collection, establishing basic dashboards, and clarifying materiality.
   - **Mid-Term (6–18 months):** Progress to more structured efforts. Include broader stakeholder engagement, developing GRI-aligned reporting, and implementing risk-based action plans.
   - **Long-Term (18–36 months):** Aim for advanced integration and external validation. Include seeking third-party disclosures, preparing for ESG ratings, and instituting robust governance reforms.

**3. Pillar-Wise Recommendations**
   - Provide 2–3 specific, actionable recommendations for **each** of the Environmental, Social, and Governance pillars.
   - For each recommendation, briefly explain its significance and tie it to relevant global ESG frameworks or standards, and suggest applicable tools or best practices.

**4. Key Tools & Metrics for Implementation**
   - Suggest 3-5 practical tools, templates, and documents that the company can use immediately to advance their ESG journey, aligned with their current maturity.
   - Examples: CDP reporting portal, SASB Materiality Map, DEI dashboard template, ESG risk register. Explain _why_ each tool is relevant.

**5. 90-Day Tactical Advisory Plan**
   - List 4–5 specific, tactical, and confidence-building actions that the company can execute within the next three months to kickstart or significantly advance their ESG efforts. These should be highly actionable.

---

🔒 Close your response with the following verbatim statement:
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
                        json={"model": "command-r", "message": prompt}
                    )
                    output = response.json()
                    recs = output.get("text") or output.get("message")
                    if recs:
                        st.subheader("📓 VerdeBot's Strategic ESG Roadmap")
                        st.markdown(recs.replace("**->**", "->")) 
                        
                        st.download_button(
                            label="⬇️ Download Roadmap as Text",
                            data=recs,
                            file_name=f"VerdeIQ_ESG_Roadmap_{info.get('name', 'Company')}_{date.today().isoformat()}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("VerdeBot did not return a roadmap. There might be an issue with the API response.")
                        st.json(output)
                else:
                    st.warning("⚠️ **Cohere API key not found.** To generate the detailed ESG roadmap, please ensure your `cohere_api_key` is configured in Streamlit secrets.")

            except requests.exceptions.RequestException as req_e:
                st.error(f"❌ Network Error communicating with VerdeBot: {req_e}. Please check your internet connection or Cohere API access.")
            except json.JSONDecodeError:
                st.error("❌ Error decoding VerdeBot's response. The API might have returned an invalid JSON.")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred while generating the roadmap: {e}")
