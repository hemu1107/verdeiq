# --- Enhanced VerdeIQ ESG Assessment App with PDF Export, AI Insights, Email & Framework Scoring ---
import streamlit as st
import json
import requests
import plotly.graph_objects as go
from pathlib import Path
from fpdf import FPDF
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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

def categorize_questions(questions):
    env = [q for q in questions if q['pillar'] == 'Environmental']
    soc = [q for q in questions if q['pillar'] == 'Social']
    gov = [q for q in questions if q['pillar'] == 'Governance']
    return env, soc, gov

env_questions, soc_questions, gov_questions = categorize_questions(questions)

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

def generate_pdf(company_info, verde_score, badge, values, recommendation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "VerdeIQ ESG Assessment Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, "Crafted by Hemaang Patkar", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Company Overview", ln=True)
    pdf.set_font("Arial", "", 12)
    for k, v in company_info.items():
        pdf.multi_cell(0, 8, f"{k}: {v}")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Assessment Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Verde Score: {verde_score}/100", ln=True)
    pdf.cell(200, 10, f"Badge Level: {badge}", ln=True)
    pdf.cell(200, 10, f"Environmental: {values[0]:.2f}/5", ln=True)
    pdf.cell(200, 10, f"Social: {values[1]:.2f}/5", ln=True)
    pdf.cell(200, 10, f"Governance: {values[2]:.2f}/5", ln=True)

    pdf.set_font("Arial", "B", 14)
    pdf.ln(10)
    pdf.cell(200, 10, "AI Recommendations", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, recommendation_text)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name

def send_email(receiver_email, pdf_path):
    sender_email = st.secrets.get("sender_email")
    sender_password = st.secrets.get("sender_password")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Your VerdeIQ ESG Report"

    body = MIMEText("Please find attached your ESG Intelligence Report by VerdeIQ.", "plain")
    msg.attach(body)

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name="VerdeIQ_ESG_Report.pdf")
        part['Content-Disposition'] = 'attachment; filename="VerdeIQ_ESG_Report.pdf"'
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

def framework_badges(score):
    if score < 30:
        return "GRI G1, BRSR Basic, SDG Awareness"
    elif score < 50:
        return "GRI G2, SASB Emerging, SDG 12"
    elif score < 70:
        return "GRI Core, SASB Moderate, TCFD Intro"
    elif score < 90:
        return "GRI Advanced, SASB Proactive, BRSR+"
    else:
        return "TCFD Aligned, GRI Comprehensive, SDG 13,14,15 Leader"

# The rest of the logic flows through 'details', 'env', 'soc', 'gov', and 'results' pages.
# Each of these pages should be implemented similarly to the intro and results page shown earlier,
# with forms to gather data, navigation control, and display logic. Let me know if you'd like
# me to continue inserting the remaining pages too!

# (continued from above)

# --- Pages ---
if st.session_state.page == "intro":
    st.markdown("<div class='title-style'>Welcome to VerdeIQ 🌿</div>", unsafe_allow_html=True)
    st.subheader("Crafted by Hemaang Patkar")
    st.markdown("""
    VerdeIQ is a modern ESG intelligence platform built to simplify ESG compliance, audit readiness, and corporate responsibility measurement.

    🚀 **Built for Analysts, PMs, CXOs & ESG Leaders**
    🌍 **Frameworks Supported**: GRI, SASB, BRSR, SDGs, TCFD
    📈 **15 High-Impact Questions** across Environmental, Social & Governance pillars

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

        if st.form_submit_button("Proceed to Environmental Assessment ➔"):
            st.session_state.page = "env"
            st.rerun()

elif st.session_state.page == "env":
    st.header("🌿 Environmental Pillar")
    st.markdown("Assess your carbon footprint, water conservation, energy use, waste management, and supply chain resilience.")
    with st.form("env_form"):
        for i, q in enumerate(env_questions):
            show_question_block(q, i, len(env_questions))
        if st.form_submit_button("Next: Social ➔"):
            st.session_state.page = "soc"
            st.rerun()

elif st.session_state.page == "soc":
    st.header("🤝 Social Pillar")
    st.markdown("Evaluate inclusivity, DEI initiatives, health & safety, learning programs, and stakeholder trust.")
    with st.form("soc_form"):
        for i, q in enumerate(soc_questions):
            show_question_block(q, i, len(soc_questions))
        if st.form_submit_button("Next: Governance ➔"):
            st.session_state.page = "gov"
            st.rerun()

elif st.session_state.page == "gov":
    st.header("🏛️ Governance Pillar")
    st.markdown("Review your board structure, ethics, cybersecurity, whistleblower policy, and data privacy.")
    with st.form("gov_form"):
        for i, q in enumerate(gov_questions):
            show_question_block(q, i, len(gov_questions))
        if st.form_submit_button("✔️ View My ESG Results"):
            st.session_state.page = "results"
            st.rerun()

elif st.session_state.page == "results":
    st.title("🌍 ESG Assessment Results")

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

    badge = "🌱 Seedling" if verde_score < 30 else "🌿 Sprout" if verde_score < 50 else "🍃 Developing" if verde_score < 70 else "🌳 Mature" if verde_score < 90 else "✨ Leader"
    tag = framework_badges(verde_score)

    st.metric(label="Verde Score", value=f"{verde_score}/100")
    st.success(f"Badge Level: {badge} — {tag}")

    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    info = st.session_state.company_info
    responses = st.session_state.responses
    detailed_answers = "\n".join([f"- {qid}: {responses[qid]}" for qid in responses])

    prompt = f"""
You are an expert ESG Consultant with 25+ years advising global companies. Create a premium ESG Strategic Report for the following firm:

🏢 **Company Overview**
- Name: {info.get('name')}
- Industry: {info.get('industry')}
- Region: {info.get('region')}
- Size: {info.get('size')}
- Listed: {info.get('public_status')}
- ESG Goals: {', '.join(info.get('esg_goals', []))}

📊 **Assessment Summary**
- Verde Score: {verde_score}/100 ({badge})
- Environmental: {values[0]:.2f}/5
- Social: {values[1]:.2f}/5
- Governance: {values[2]:.2f}/5

📝 **Assessment Answers**
{detailed_answers}

Generate the following in markdown:
1. Summary & Risk Profile
2. Strategic Roadmap (Quick Wins, Mid-term, Long-term)
3. Pillar Analysis (Gaps & Recommendations)
4. Toolkits & Software
5. Case Study Examples
6. KPIs & Milestones
7. Risk Mitigation
8. Call-to-Action
"""

    with st.spinner("Generating your ESG Roadmap..."):
        api_key = st.secrets.get("cohere_api_key")
        if api_key:
            res = requests.post(
                url="https://api.cohere.ai/v1/chat",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "command-r-plus", "message": prompt}
            )
            output = res.json()
            recs = output.get("text") or output.get("response") or "No recommendations generated."
            st.subheader("📓 Premium ESG Recommendations")
            st.markdown(recs)

            pdf_path = generate_pdf(info, verde_score, badge, values, recs)
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download PDF Report", f, file_name="VerdeIQ_ESG_Report.pdf")

            email = st.text_input("📧 Send this report via email")
            if st.button("Send Email") and email:
                send_email(email, pdf_path)
                st.success("Email sent successfully!")
        else:
            st.warning("Missing Cohere API key in secrets")


