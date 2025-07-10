# --- Enhanced VerdeIQ ESG Assessment App ---
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
    st.markdown("<div class='title-style'>Welcome to VerdeIQ !</div>", unsafe_allow_html=True)
    st.subheader("ESG Intelligence Simplified")

    st.caption("Crafted by Hemaang Patkar")
    
    st.markdown("""
    VerdeIQ is your AI-powered ESG self-assessment platform.

    - 💡 Answer 15 core ESG questions
    - 📊 Get scored within 0-100 to understand current ESG Maturity Standing
    - 🌍 Frameworks aligned include **GRI**, **SASB**, **BRSR**, and **UN SDGs**
    - ⚡ Get Instant Reccomendations & Detailed Roadmap within mins!

    **Score Tiers:**
    - 🌱 Seedling (0–29)
    - 🌿 Sprout (30–49)
    - 🍃 Developing (50–69)
    - 🌳 Mature (70–89)
    - ✨ Leader (90–100)
    """)
    if st.button("Start ESG Assessment ➔"):
        st.session_state.page = "details"
        st.rerun()

elif st.session_state.page == "details":
    st.title("🏢 Organization Profile")
    with st.form("org_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.company_info['name'] = st.text_input("Company Name")
            st.session_state.company_info['industry'] = st.text_input("Industry")
            st.session_state.company_info['location'] = st.text_input("City")
        with c2:
            st.session_state.company_info['size'] = st.selectbox("Team Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
            st.session_state.company_info['esg_goals'] = st.multiselect("Key ESG Priorities", [
                "Carbon Neutrality", "DEI", "Data Privacy", "Green Reporting", "Compliance", "Community Engagement"])
            st.session_state.company_info['public_status'] = st.radio("Is your company publicly listed?", ["Yes", "No", "Planning to"])
        st.session_state.company_info['region'] = st.selectbox("Primary Operational Region", ["North America", "Europe", "Asia-Pacific", "Middle East", "Africa", "Global"])
        st.session_state.company_info['years_operating'] = st.slider("Years in Operation", 0, 100, 5)

        if st.form_submit_button("Proceed to Assessment ➔"):
            st.session_state.page = "env"
            st.rerun()

elif st.session_state.page == "env":
    st.header("Environment 🌿")
    st.markdown("Assess your carbon, water, waste, and energy practices.")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.form_submit_button("Next: Social ➔"):
            st.session_state.page = "soc"
            st.rerun()

elif st.session_state.page == "soc":
    st.header("Social 🤝")
    st.markdown("Evaluate team development, DEI, wellness, and community actions.")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.form_submit_button("Next: Governance ➔"):
            st.session_state.page = "gov"
            st.rerun()

elif st.session_state.page == "gov":
    st.header("Governance 🏛️")
    st.markdown("Leadership, ethics, data privacy, and board diversity.")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.form_submit_button("✔️ View My ESG Results"):
            st.session_state.page = "results"
            st.rerun()

elif st.session_state.page == "results":
    st.title("🌿 ESG Assessment Results")
    verde_score, scores, counts = calculate_scores(st.session_state.responses)

    labels = list(scores.keys())
    values = [scores[k] / counts[k] if counts[k] else 0 for k in labels]

    st.metric(label="Verde Score", value=f"{verde_score}/100")

    badge = "🌱 Seedling" if verde_score < 30 else \
            "🌿 Sprout" if verde_score < 50 else \
            "🍃 Developing" if verde_score < 70 else \
            "🌳 Mature" if verde_score < 90 else "✨ Leader"

    st.success(f"Badge Level: {badge}")

    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- Deep ESG Consulting Prompt ---
    try:
        info = st.session_state.company_info
        responses = st.session_state.responses
        detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])
        prompt = f"""
You are an experienced ESG Consultant tasked with drafting a precise, framework-aligned ESG Summary and Roadmap for the following company based on their self-assessment inputs.

The report must reflect:
- Only what is **true based on responses** (avoid assumptions or fake metrics).
- Clear alignment with global ESG frameworks such as **GRI**, **SASB**, **BRSR**, and **SDGs** (mapped per question).
- Professional tone suitable for ESG officers or investors.

---

🏢 **Company Overview**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Team Size: {info.get('size')}
- Public Status: {info.get('public_status')}
- Region: {info.get('region')}
- Years in Operation: {info.get('years_operating')} years
- ESG Focus Areas: {', '.join(info.get('esg_goals', [])) or 'Not specified'}

📊 **Assessment Summary**
- VerdeIQ Score: {verde_score}/100
- Badge: {badge}
- Environmental Maturity: {values[0]:.2f}/5
- Social Maturity: {values[1]:.2f}/5
- Governance Maturity: {values[2]:.2f}/5

---

🎯 **Deliver the following sections:**

### 1. ESG Profile Summary
- Key strengths based on top-rated responses
- Gaps based on lowest-rated areas
- Mention ESG frameworks that relate to each pillar (e.g., GRI 305 for emissions)

### 2. Customized Roadmap
Structure it as:
- **Immediate Next Steps (0–6 months)** – small internal actions or policy creation
- **Medium-Term (6–18 months)** – tracking, tool adoption, formalization
- **Long-Term (18–36 months)** – disclosure, audits, certifications
Do **not** mention budgets unless tied to an actual response (e.g., if they say “We publish ESG reports”, you may suggest external audits)

### 3. Pillar-Wise Breakdown
For each of Environmental, Social, and Governance:
- Highlight top 1–2 strengths and top 1–2 improvement areas
- Connect each point to a relevant ESG framework (like GRI 404 for employee training, GRI 418 for data privacy)

### 4. Tool & Template Suggestions
Only suggest tools or templates that match their current stage (e.g., spreadsheets vs dashboards vs audit software)
Mention practical tools (e.g., GHG Protocol, SDG Tracker, DEI dashboards, Conflict of Interest policy templates)

### 5. Closing Advisory
Short advisory note: What should they do in the next 90 days to advance ESG maturity confidently?

---

🧠 Responses:
{detailed_answers}

Use structured markdown format and avoid vague phrases like "you should consider..." — instead, use confident, actionable sentences. Avoid artificial metrics unless implied by the company’s responses.
"""


        try:
    with st.spinner("""
🔍 Generating your ESG Intelligence Report...

We're analyzing your inputs across the **Environmental, Social, and Governance** pillars, aligning them with leading frameworks like **GRI**, **SASB**, **BRSR**, and **UN SDGs**.

Please hold on while we prepare:
- 📊 Maturity Assessment Summary
- 🗺️ Strategic ESG Roadmap
- 🧰 Toolkits & Practical Recommendations
- 🎯 Key KPIs and 90-Day Advisory Plan

This may take up to **a minute**. Thanks for your patience while we create a report that reflects a high-quality consulting output!
"""):
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
            st.subheader("📓 Premium ESG Recommendations")
            st.markdown(recs)
        else:
            st.warning("⚠️ Cohere API key not found in secrets. Please add `cohere_api_key` to your `.streamlit/secrets.toml` file.")
except Exception as e:
    st.error(f"❌ An error occurred while generating recommendations: {e}")


    st.download_button("Download ESG Report", data=json.dumps({
        "Company": st.session_state.company_info,
        "Score": verde_score,
        "Badge": badge,
        "Pillar Scores": dict(zip(labels, values)),
        "Answers": st.session_state.responses
    }, indent=2), file_name="verdeiq_esg_report.json")

    st.caption("Crafted by Hemaang Patkar")
