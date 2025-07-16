# --- Enhanced VerdeIQ ESG Assessment App with Industry-Specific Scoring ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# --- Configuration ---
st.set_page_config(page_title="VerdeIQ | ESG Intelligence", layout="centered", page_icon="🌿")

# --- Styling & Theming ---
st.markdown("""
    <style>
        .title-style {font-size: 32px; font-weight: bold; color: #228B22;}
        .section-title {font-size: 20px; font-weight: 600; margin-top: 20px;}
        .back-button {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px 10px;
            color: #666;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 10px;
        }
        .progress-bar {
            width: 100%;
            height: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .progress-fill {
            height: 100%;
            background-color: #228B22;
            transition: width 0.3s ease;
        }
        .response-summary {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #228B22;
        }
    </style>
""", unsafe_allow_html=True)

# --- Industry-Specific Weighting System (SASB-aligned) ---
INDUSTRY_WEIGHTS = {
    "Manufacturing": {
        "Environmental": 0.45,  # Higher weight for manufacturing
        "Social": 0.25,
        "Governance": 0.30
    },
    "IT/Services": {
        "Environmental": 0.25,  # Lower environmental weight
        "Social": 0.40,         # Higher social weight (data privacy, workforce)
        "Governance": 0.35
    },
    "Finance": {
        "Environmental": 0.20,  # Lowest environmental weight
        "Social": 0.35,
        "Governance": 0.45      # Highest governance weight
    },
    "Healthcare": {
        "Environmental": 0.30,
        "Social": 0.45,         # Highest social weight (patient safety, access)
        "Governance": 0.25
    },
    "Energy": {
        "Environmental": 0.50,  # Highest environmental weight
        "Social": 0.25,
        "Governance": 0.25
    },
    "Consumer Goods": {
        "Environmental": 0.40,
        "Social": 0.35,
        "Governance": 0.25
    },
    "Transportation": {
        "Environmental": 0.45,
        "Social": 0.30,
        "Governance": 0.25
    },
    "Real Estate": {
        "Environmental": 0.40,
        "Social": 0.30,
        "Governance": 0.30
    },
    "Other": {
        "Environmental": 0.33,
        "Social": 0.33,
        "Governance": 0.34
    }
}

# --- Load ESG Questions JSON ---
@st.cache_data
def load_questions():
    # For demo purposes, using sample questions
    return [
        {
            "id": "ENV001",
            "question": "How does your organization track and report greenhouse gas emissions?",
            "pillar": "Environmental",
            "options": ["No tracking system", "Basic tracking", "Comprehensive tracking", "Third-party verified tracking", "Science-based targets with verification"],
            "frameworks": ["GRI 305", "SASB", "CDP"],
            "industry_relevance": {
                "Manufacturing": "high",
                "Energy": "high",
                "IT/Services": "medium",
                "Finance": "low",
                "Healthcare": "medium"
            },
            "time_sensitive": True
        },
        {
            "id": "ENV002",
            "question": "What is your organization's approach to waste management and circular economy practices?",
            "pillar": "Environmental",
            "options": ["No formal approach", "Basic waste reduction", "Systematic waste management", "Circular economy initiatives", "Zero waste to landfill certified"],
            "frameworks": ["GRI 306", "SASB", "SDG 12"],
            "industry_relevance": {
                "Manufacturing": "high",
                "Consumer Goods": "high",
                "IT/Services": "medium",
                "Finance": "low",
                "Healthcare": "high"
            },
            "time_sensitive": True
        },
        {
            "id": "SOC001",
            "question": "How does your organization ensure diversity, equity, and inclusion in the workplace?",
            "pillar": "Social",
            "options": ["No formal program", "Basic policies", "Structured DEI program", "Comprehensive with metrics", "Industry-leading with external recognition"],
            "frameworks": ["GRI 405", "SASB", "SDG 5"],
            "industry_relevance": {
                "IT/Services": "high",
                "Finance": "high",
                "Healthcare": "high",
                "Manufacturing": "medium",
                "Energy": "medium"
            },
            "time_sensitive": True
        },
        {
            "id": "SOC002",
            "question": "What measures are in place to protect employee health and safety?",
            "pillar": "Social",
            "options": ["Basic compliance", "Standard safety protocols", "Comprehensive safety management", "Proactive safety culture", "Zero-incident target with industry recognition"],
            "frameworks": ["GRI 403", "SASB", "SDG 3"],
            "industry_relevance": {
                "Manufacturing": "high",
                "Healthcare": "high",
                "Energy": "high",
                "IT/Services": "medium",
                "Finance": "low"
            },
            "time_sensitive": True
        },
        {
            "id": "GOV001",
            "question": "How is ESG oversight integrated into your board governance structure?",
            "pillar": "Governance",
            "options": ["No ESG oversight", "Ad-hoc ESG discussions", "ESG committee", "Dedicated ESG board committee", "ESG integrated across all board decisions"],
            "frameworks": ["GRI 2-9", "SASB", "TCFD"],
            "industry_relevance": {
                "Finance": "high",
                "Energy": "high",
                "Healthcare": "high",
                "IT/Services": "medium",
                "Manufacturing": "medium"
            },
            "time_sensitive": False
        }
    ]

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
    st.session_state.response_timestamps = {}
    st.session_state.navigation_history = []

# --- Navigation Functions ---
def show_progress():
    total_questions = len(questions)
    answered_questions = len(st.session_state.responses)
    progress = (answered_questions / total_questions) * 100
    
    st.markdown(f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
    </div>
    <p>Progress: {answered_questions}/{total_questions} questions answered ({progress:.1f}%)</p>
    """, unsafe_allow_html=True)

def show_back_button(previous_page):
    if st.button("← Back", key="back_btn"):
        st.session_state.page = previous_page
        st.rerun()

def show_response_summary():
    if st.session_state.responses:
        st.subheader("📋 Current Responses Summary")
        for q in questions:
            if q['id'] in st.session_state.responses:
                response = st.session_state.responses[q['id']]
                timestamp = st.session_state.response_timestamps.get(q['id'], 'Not recorded')
                
                # Show time sensitivity indicator
                time_indicator = "🕐" if q.get('time_sensitive', False) else "📋"
                
                st.markdown(f"""
                <div class="response-summary">
                    <strong>{time_indicator} {q['id']}: {q['question']}</strong><br>
                    <em>Response:</em> {response}<br>
                    <small>Last updated: {timestamp}</small>
                </div>
                """, unsafe_allow_html=True)

# --- Industry-Specific Scoring ---
def calculate_industry_weighted_scores(responses, industry):
    weights = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS["Other"])
    
    pillar_scores = {"Environmental": 0, "Social": 0, "Governance": 0}
    pillar_counts = {"Environmental": 0, "Social": 0, "Governance": 0}
    total_score = 0
    max_possible = 0

    for q in questions:
        if q['id'] in responses:
            score = q["options"].index(responses[q["id"]])
            max_score = len(q["options"]) - 1
            
            # Apply industry-specific relevance multiplier
            relevance = q.get('industry_relevance', {}).get(industry, 'medium')
            relevance_multiplier = {'high': 1.2, 'medium': 1.0, 'low': 0.8}.get(relevance, 1.0)
            
            weighted_score = score * relevance_multiplier
            pillar_scores[q["pillar"]] += weighted_score
            pillar_counts[q["pillar"]] += 1
            
            total_score += weighted_score
            max_possible += max_score * relevance_multiplier

    # Apply pillar weights
    final_score = 0
    for pillar in pillar_scores:
        if pillar_counts[pillar] > 0:
            pillar_avg = pillar_scores[pillar] / pillar_counts[pillar]
            final_score += pillar_avg * weights[pillar]
    
    verde_score = round((final_score / 4) * 100)  # Normalize to 0-100
    return verde_score, pillar_scores, pillar_counts, weights

# --- Helper Functions ---
def show_question_block(q, idx, total):
    # Industry relevance indicator
    industry = st.session_state.company_info.get('sector_type', 'Other')
    relevance = q.get('industry_relevance', {}).get(industry, 'medium')
    relevance_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
    
    st.markdown(f"**{q['id']}: {q['question']}**")
    st.caption(f"Industry Relevance: {relevance_emoji[relevance]} {relevance.title()}")
    
    if q.get('frameworks'):
        st.caption(f"Frameworks: {', '.join(q['frameworks'])}")
    
    # Time sensitivity indicator
    if q.get('time_sensitive', False):
        st.caption("🕐 Time-sensitive: Regular updates recommended")
    
    current_response = st.session_state.responses.get(q['id'], q['options'][0])
    response = st.radio(
        label=f"Assessment {idx + 1} of {total}",
        options=q['options'],
        index=q['options'].index(current_response) if current_response in q['options'] else 0,
        key=f"{q['id']}_radio"
    )
    
    # Store response with timestamp
    st.session_state.responses[q['id']] = response
    st.session_state.response_timestamps[q['id']] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st.markdown("---")

# --- Agentic Copilot Introduction ---
def introduce_agent():
    st.info("🤖 Meet VerdeBot: Your Industry-Aware ESG Copilot")
    st.caption("VerdeBot now uses industry-specific weightings based on SASB standards, ensuring your assessment reflects what matters most for your sector.")

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Your Industry-Aware ESG Copilot")
    st.caption("Enhanced with Senior ESG Analyst feedback - Crafted by Hemaang Patkar")
    
    introduce_agent()
    
    st.markdown("""
    **🆕 What's New:**
    - 🏭 **Industry-Specific Scoring**: Weighted assessments based on SASB industry classifications
    - 🕐 **Time-Sensitive Tracking**: Timestamps for policy updates and regular reviews
    - 🔄 **Enhanced Navigation**: Review and edit responses before final submission
    - 📊 **Relevance Indicators**: See which questions matter most for your industry
    
    **Assessment Features:**
    - 🤖 Agentic Persona: VerdeBot interprets your responses with industry context
    - 🔎 Industry-calibrated prompts mapped to global frameworks
    - 📊 Real-time contextual scoring and advisory
    - 🛍️ Roadmaps curated to your company's size, maturity, and sector

    **Maturity Tiers:**
    - 🌱 Seedling (0–29)
    - 🌿 Sprout (30–49)
    - 🍃 Developing (50–69)
    - 🌳 Mature (70–89)
    - ✨ Leader (90–100)
    """)
    
    if st.button("Launch Enhanced ESG Assessment →"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Enhanced Company Profile Setup")
    st.caption("VerdeBot is learning your company DNA for industry-specific analysis...")
    
    show_progress()
    
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
            
            # Enhanced sector selection with SASB alignment
            st.session_state.company_info['sector_type'] = st.selectbox("Sector Type (SASB-aligned)", 
                ["Manufacturing", "IT/Services", "Finance", "Healthcare", "Energy", "Consumer Goods", "Transportation", "Real Estate", "Other"])
            
            st.session_state.company_info['esg_team_size'] = st.selectbox("Dedicated ESG Team Size", ["0", "1-2", "3-5", "6-10", "10+"])
            st.session_state.company_info['internal_esg_training'] = st.radio("Internal ESG Training Programs?", ["Yes", "No"])
            st.session_state.company_info['climate_risk_policy'] = st.radio("Climate Risk Mitigation Policy?", ["Yes", "No"])
            st.session_state.company_info['regulatory_exposure'] = st.selectbox("Regulatory Exposure", ["Low", "Moderate", "High"])

        st.session_state.company_info['region'] = st.selectbox("Main Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"])
        st.session_state.company_info['years_operating'] = st.slider("Years Since Founding", 0, 200, 5)
        
        # Last ESG review date
        st.session_state.company_info['last_esg_review'] = st.date_input("Last Comprehensive ESG Review", value=datetime.now().date() - timedelta(days=365))

        if st.form_submit_button("Begin Industry-Specific Assessment →"):
            st.session_state.page = "env"
            st.rerun()

elif st.session_state.page == "env":
    st.header("🌿 Environmental Evaluation")
    industry = st.session_state.company_info.get('sector_type', 'Other')
    weight = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS['Other'])['Environmental']
    st.caption(f"Industry Weight: {weight:.0%} | Analyzing your sustainability posture...")
    
    show_progress()
    show_back_button("details")
    
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Continue to Social 🤝"):
                st.session_state.page = "soc"
                st.rerun()
        with col2:
            if st.form_submit_button("Review All Responses 📋"):
                st.session_state.page = "review"
                st.rerun()

elif st.session_state.page == "soc":
    st.header("🤝 Social Assessment")
    industry = st.session_state.company_info.get('sector_type', 'Other')
    weight = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS['Other'])['Social']
    st.caption(f"Industry Weight: {weight:.0%} | Analyzing your team, culture, and external impact...")
    
    show_progress()
    show_back_button("env")
    
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Continue to Governance 🏛️"):
                st.session_state.page = "gov"
                st.rerun()
        with col2:
            if st.form_submit_button("Review All Responses 📋"):
                st.session_state.page = "review"
                st.rerun()

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Assessment")
    industry = st.session_state.company_info.get('sector_type', 'Other')
    weight = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS['Other'])['Governance']
    st.caption(f"Industry Weight: {weight:.0%} | Parsing leadership ethics and oversight structures...")
    
    show_progress()
    show_back_button("soc")
    
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Review All Responses 📋"):
                st.session_state.page = "review"
                st.rerun()
        with col2:
            if st.form_submit_button("Generate Analysis ✨"):
                st.session_state.page = "results"
                st.rerun()

elif st.session_state.page == "review":
    st.title("📋 Response Review & Edit")
    st.caption("Review all your responses before generating the final analysis. You can edit any response below.")
    
    show_progress()
    show_back_button("gov")
    
    # Show current industry weighting
    industry = st.session_state.company_info.get('sector_type', 'Other')
    weights = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS['Other'])
    
    st.subheader(f"Industry Weighting for {industry}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Environmental", f"{weights['Environmental']:.0%}")
    with col2:
        st.metric("Social", f"{weights['Social']:.0%}")
    with col3:
        st.metric("Governance", f"{weights['Governance']:.0%}")
    
    # Editable responses
    st.subheader("Edit Your Responses")
    
    for pillar in ["Environmental", "Social", "Governance"]:
        st.markdown(f"### {pillar}")
        pillar_questions = [q for q in questions if q['pillar'] == pillar]
        
        for q in pillar_questions:
            current_response = st.session_state.responses.get(q['id'], q['options'][0])
            relevance = q.get('industry_relevance', {}).get(industry, 'medium')
            relevance_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            
            new_response = st.selectbox(
                f"{relevance_emoji[relevance]} {q['id']}: {q['question']}",
                q['options'],
                index=q['options'].index(current_response) if current_response in q['options'] else 0,
                key=f"review_{q['id']}"
            )
            
            # Update response if changed
            if new_response != current_response:
                st.session_state.responses[q['id']] = new_response
                st.session_state.response_timestamps[q['id']] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Show last updated
            timestamp = st.session_state.response_timestamps.get(q['id'], 'Not recorded')
            st.caption(f"Last updated: {timestamp}")
    
    if st.button("Generate Industry-Specific Analysis ✨"):
        st.session_state.page = "results"
        st.rerun()

elif st.session_state.page == "results":
    st.title("📊 VerdeIQ Industry-Specific ESG Analysis")
    
    industry = st.session_state.company_info.get('sector_type', 'Other')
    verde_score, scores, counts, weights = calculate_industry_weighted_scores(st.session_state.responses, industry)
    
    labels = list(scores.keys())
    values = [scores[k] / counts[k] if counts[k] else 0 for k in labels]

    badge = "🌱 Seedling" if verde_score < 30 else \
            "🌿 Sprout" if verde_score < 50 else \
            "🍃 Developing" if verde_score < 70 else \
            "🌳 Mature" if verde_score < 90 else "✨ Leader"

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Industry-Adjusted ESG Score", value=f"{verde_score}/100")
    with col2:
        st.metric(label="Maturity Tier", value=badge)

    st.success(f"📍 Industry: {industry} | Scoring calibrated to sector-specific materiality")

    # Industry-weighted radar chart
    st.subheader("Industry-Weighted Performance Radar")
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        name='Your Performance'
    ))
    
    # Add industry weighting as reference
    weight_values = [weights[pillar] * 5 for pillar in labels]  # Scale to 0-5
    fig.add_trace(go.Scatterpolar(
        r=weight_values,
        theta=labels,
        fill='toself',
        name='Industry Weight',
        opacity=0.3,
        line=dict(color='orange')
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
        title="Performance vs Industry Materiality"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Time-sensitive alerts
    st.subheader("🕐 Time-Sensitive Recommendations")
    now = datetime.now()
    last_review = st.session_state.company_info.get('last_esg_review')
    
    if last_review and (now.date() - last_review).days > 365:
        st.warning("⚠️ Your last comprehensive ESG review was over a year ago. Consider scheduling an update.")
    
    # Show which responses need regular updates
    time_sensitive_questions = [q for q in questions if q.get('time_sensitive', False)]
    if time_sensitive_questions:
        st.info("📅 The following areas require regular monitoring and updates:")
        for q in time_sensitive_questions:
            st.caption(f"• {q['id']}: {q['question']}")

    # Enhanced roadmap generation
    if st.button("🔍 Generate Industry-Specific ESG Roadmap"):
        with st.spinner("🔍 VerdeBot is generating your industry-calibrated ESG roadmap..."):
            try:
                info = st.session_state.company_info
                responses = st.session_state.responses
                detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])
                
                # Include industry-specific context
                industry_context = f"""
                **Industry-Specific Context:**
                - Sector: {industry}
                - Environmental Weight: {weights['Environmental']:.0%}
                - Social Weight: {weights['Social']:.0%}
                - Governance Weight: {weights['Governance']:.0%}
                - Industry-Adjusted Score: {verde_score}/100
                """
                
                prompt = f"""You are VerdeBot, an advanced Industry-Aware ESG Copilot with deep expertise in sector-specific sustainability practices. You have just completed an industry-weighted ESG assessment based on SASB materiality frameworks.

{industry_context}

🏢 **Company Profile**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Sector Type: {info.get('sector_type')}
- Team Size: {info.get('size')}
- Last ESG Review: {info.get('last_esg_review')}
- Industry-Adjusted VerdeIQ Score: {verde_score}/100
- Badge: {badge}

📊 **Industry-Weighted Assessment Results**
{detailed_answers}

🎯 **Your Task as Industry-Aware VerdeBot**

Generate a comprehensive ESG roadmap that:
1. Prioritizes actions based on industry materiality (higher weight = higher priority)
2. Addresses time-sensitive elements that need regular updates
3. Provides sector-specific benchmarks and best practices
4. Includes relevant industry peers and standards

Structure your response with:
1. **Industry Context & Materiality Analysis**
2. **Sector-Specific Strengths & Gaps**
3. **Industry-Prioritized 36-Month Roadmap**
4. **Time-Sensitive Action Items**
5. **Industry Peer Benchmarking**
6. **Sector-Relevant Tools & Resources**

Focus on what matters most for the {industry} sector while maintaining alignment with global ESG frameworks.

Close with: "This industry-calibrated roadmap was synthesized by VerdeBot — your intelligent ESG copilot engineered for sector-specific sustainability excellence."
"""

                # Use mock response for demo
                st.subheader("📓 Industry-Specific ESG Roadmap")
                st.markdown(f"""
                ## Industry Context & Materiality Analysis
                
                For the **{industry}** sector, your ESG priorities are calibrated as follows:
                - **Environmental**: {weights['Environmental']:.0%} weight (industry materiality consideration)
                - **Social**: {weights['Social']:.0%} weight
                - **Governance**: {weights['Governance']:.0%} weight
                
                ## Key Findings for {industry}
                
                **Strengths:**
                - Your current score of {verde_score}/100 places you in the {badge} tier
                - Industry-specific weighting has been applied to ensure relevance
                
                **Priority Actions (Next 6 Months):**
                1. Focus on highest-weighted pillar areas for your sector
                2. Update time-sensitive policies and procedures
                3. Conduct industry peer benchmarking
                
                **Industry-Specific Recommendations:**
                - Align with sector-specific SASB standards
                - Consider industry-relevant ESG rating agencies
                - Implement sector best practices for material topics
                
                ---
                
                *This industry-calibrated roadmap was synthesized by VerdeBot — your intelligent ESG copilot engineered for sector-specific sustainability excellence.*
                """)
                
            except Exception as e:
                st.error(f"❌ Error generating roadmap: {e}")
    
    # Navigation options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Retake Assessment"):
            # Reset session state
            st.session_state.responses = {}
            st.session_state.response_timestamps = {}
            st.session_state.page = "details"
            st.rerun()
    
    with col2:
        if st.button("📝 Edit Responses"):
            st.session_state.page = "review"
            st.rerun()
    
    with col3:
        if st.button("📊 Export Results"):
            # Create export data
            export_data = {
                "company_info": st.session_state.company_info,
                "responses": st.session_state.responses,
                "timestamps": st.session_state.response_timestamps,
                "industry_weights": weights,
                "verde_score": verde_score,
                "badge": badge,
                "assessment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.download_button(
                label="Download Assessment Report",
                data=json.dumps(export_data, indent=2, default=str),
                file_name=f"VerdeIQ_Assessment_{info.get('name', 'Company')}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

# --- Additional Features ---

# Add a sidebar for quick navigation
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    
    # Show current page
    page_names = {
        "intro": "🏠 Introduction",
        "details": "🏢 Company Profile",
        "env": "🌿 Environmental",
        "soc": "🤝 Social",
        "gov": "🏛️ Governance",
        "review": "📋 Review Responses",
        "results": "📊 Results & Analysis"
    }
    
    current_page = page_names.get(st.session_state.page, "Unknown")
    st.success(f"Current: {current_page}")
    
    # Show completion status
    if st.session_state.responses:
        completion = len(st.session_state.responses) / len(questions) * 100
        st.progress(completion / 100)
        st.caption(f"Assessment: {completion:.1f}% complete")
    
    # Quick navigation buttons (only if user has progressed)
    if st.session_state.page not in ["intro", "details"]:
        st.markdown("### 🔗 Quick Links")
        if st.button("🏢 Company Profile", key="sidebar_details"):
            st.session_state.page = "details"
            st.rerun()
        
        if st.session_state.responses:
            if st.button("📋 Review Responses", key="sidebar_review"):
                st.session_state.page = "review"
                st.rerun()
        
        if len(st.session_state.responses) == len(questions):
            if st.button("📊 View Results", key="sidebar_results"):
                st.session_state.page = "results"
                st.rerun()
    
    # Show industry-specific info
    if st.session_state.company_info.get('sector_type'):
        industry = st.session_state.company_info['sector_type']
        st.markdown("### 🏭 Industry Context")
        st.info(f"**Sector:** {industry}")
        
        weights = INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS['Other'])
        st.caption("**Materiality Weights:**")
        st.caption(f"🌿 Environmental: {weights['Environmental']:.0%}")
        st.caption(f"🤝 Social: {weights['Social']:.0%}")
        st.caption(f"🏛️ Governance: {weights['Governance']:.0%}")
    
    # Help section
    st.markdown("### ❓ Help")
    with st.expander("Industry Weights Explained"):
        st.markdown("""
        **Industry-specific weights** are based on SASB (Sustainability Accounting Standards Board) materiality assessments:
        
        - **Manufacturing**: Higher environmental weight due to emissions and resource use
        - **IT/Services**: Higher social weight for data privacy and workforce issues
        - **Finance**: Higher governance weight for regulatory compliance
        - **Healthcare**: Higher social weight for patient safety and access
        - **Energy**: Highest environmental weight for climate impact
        """)
    
    with st.expander("Time-Sensitive Indicators"):
        st.markdown("""
        **🕐 Time-sensitive questions** require regular updates:
        
        - Emissions tracking data
        - Policy review dates
        - Training completion rates
        - Audit schedules
        
        These should be reviewed quarterly or annually.
        """)
    
    with st.expander("Relevance Indicators"):
        st.markdown("""
        **Industry relevance** shows how important each question is for your sector:
        
        - 🔴 **High**: Critical for your industry
        - 🟡 **Medium**: Important but not critical
        - 🟢 **Low**: Nice to have but low priority
        """)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>VerdeIQ</strong> - Industry-Aware ESG Intelligence Platform</p>
    <p>Enhanced with Senior ESG Analyst feedback | Powered by SASB-aligned materiality frameworks</p>
    <p>Developed by <em>Hemaang Patkar</em> | Version 2.0 - Industry-Specific Edition</p>
</div>
""", unsafe_allow_html=True)
