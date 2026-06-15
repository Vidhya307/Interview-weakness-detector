import os
import json
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
from generator import generate_questions
from evaluator import evaluate_answer
from tracker import _average_scores
from database import init_db, save_session, get_sessions, get_weakest_dim
from auth import show_login_page, logout

load_dotenv()

import streamlit as st

def get_secret(key):
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, "")

st.set_page_config(
    page_title="Interview Coach AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"  # ← add this
)
# ── Global styles ─────────────────────────────────────────
st.markdown("""
<style>
/* Hide ALL Streamlit branding and toolbar */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
[data-testid="stToolbarActions"] {display: none !important;}
.stDeployButton {display: none !important;}
[data-testid="baseButton-headerNoPadding"] {display: none !important;}

/* Hide bottom right floating buttons (the ones circled) */
.st-emotion-cache-zq5wmm {display: none !important;}
.st-emotion-cache-1wbqy5l {display: none !important;}
[class*="StatusWidget"] {display: none !important;}
[class*="viewerBadge"] {display: none !important;}
#GithubIcon {display: none !important;}
]
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0B0D1B; }

[data-testid="stSidebar"] {
    background: #12152A !important;
    border-right: 1px solid #2A2D4A;
}
}
[data-testid="metric-container"] {
    background: #181C33;
    border: 1px solid #2A2D4A;
    border-radius: 10px;
    padding: 16px !important;
    transition: border-color 200ms;
}
[data-testid="metric-container"]:hover { border-color: #514A85; }

.stButton > button {
    background: #5F01FB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 200ms !important;
    width: 100%;
}
.stButton > button:hover { background: #3D0099 !important; }

[data-testid="stExpander"] {
    background: #181C33;
    border: 1px solid #2A2D4A;
    border-radius: 10px;
}
.stProgress > div > div { background: #5F01FB !important; }
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea textarea {
    background: #181C33 !important;
    border: 1px solid #2A2D4A !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}
hr { border-color: #2A2D4A !important; }
h1, h2, h3 { color: #FFFFFF !important; }
p, label, .stMarkdown { color: #A8A8C0; }
</style>
""", unsafe_allow_html=True)

# ── Auth gate ─────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    show_login_page()
    st.stop()

# ── Resume reader ─────────────────────────────────────────
def read_resume(uploaded_file):
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text[:4000]
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")[:4000]

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 0 8px 0;text-align:center">
        <div style="font-size:36px">🎯</div>
        <div style="font-size:17px;font-weight:700;background:linear-gradient(135deg,#a78bfa,#818cf8);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:4px">
             Interview Coach AI
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navigate", [
        "🏠 Dashboard",
        "🎤 Practice",
        "📈 Progress",
        "📋 Question Bank",
        "📄 Resume Evaluator",
        "🎥 Interview Room",
    ], label_visibility="collapsed")

    st.divider()

    uid = st.session_state.user["id"]
    sessions = get_sessions(uid)
    dims = ["clarity","specificity","relevance","structure","impact"]

    st.markdown(f"""
    <div style="background:#1f2937;border-radius:10px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:#9ca3af">
        👤 <b style="color:#e5e7eb">{st.session_state.user['username']}</b>
    </div>
    <div style="background:#1f2937;border-radius:10px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:#9ca3af">
        Sessions: <b style="color:#e5e7eb">{len(sessions)}</b>
    </div>
    """, unsafe_allow_html=True)

    if sessions:
        avg_all = {d: round(sum(s["avg_scores"].get(d,0) for s in sessions)/len(sessions),1) for d in dims}
        overall_sb = round(sum(avg_all.values())/5, 1)
        weakest_sb = min(avg_all, key=avg_all.get)
        st.markdown(f"""
        <div style="background:#1f2937;border-radius:10px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:#9ca3af">
            Avg score: <b style="color:#e5e7eb">{overall_sb} / 5</b>
        </div>
        <div style="background:#1f2937;border-radius:10px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:#9ca3af">
            Focus on: <b style="color:#a78bfa">{weakest_sb.capitalize()}</b>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("Logout"):
        logout()

# ══════════════════════════════════════════════════════════
# 🏠  DASHBOARD
# ══════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="page-header">
        <h1>🏠 Dashboard</h1>
        <p>Your interview training overview at a glance</p>
    </div>""", unsafe_allow_html=True)

    sessions = get_sessions(uid)

    if not sessions:
        st.info("No sessions yet. Go to **Practice** or **🎥 Interview Room** to begin!")
    else:
        avg_scores = {d: round(sum(s["avg_scores"].get(d,0) for s in sessions)/len(sessions),2) for d in dims}
        overall    = round(sum(avg_scores.values())/5, 1)
        weakest    = min(avg_scores, key=avg_scores.get)
        best       = max(avg_scores, key=avg_scores.get)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🗂 Sessions",   len(sessions))
        c2.metric("⭐ Avg Score",  f"{overall} / 5")
        c3.metric("🏆 Best",       best.capitalize(),    f"{avg_scores[best]:.1f}")
        c4.metric("🎯 Focus on",   weakest.capitalize(), f"{avg_scores[weakest]:.1f}", delta_color="inverse")

        st.divider()
        col_l, col_r = st.columns([1.3, 1])

        with col_l:
            st.subheader("📊 Dimension breakdown")
            colors = ["#10b981" if avg_scores[d]>=4 else "#f59e0b" if avg_scores[d]>=3 else "#ef4444" for d in dims]
            fig = go.Figure(go.Bar(
                x=list(avg_scores.values()),
                y=[d.capitalize() for d in dims],
                orientation="h",
                marker_color=colors,
                text=[f"{v:.1f}" for v in avg_scores.values()],
                textposition="outside"
            ))
            fig.update_layout(
                xaxis=dict(range=[0,5], gridcolor="#1f2937"),
                height=260, margin=dict(l=0,r=50,t=10,b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9ca3af")
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("🎯 What to focus on")
            tips = {
                "clarity":     "Structure in 3 parts. Cut filler words.",
                "specificity": "Use real numbers, names, tools.",
                "relevance":   "Re-read the question before answering.",
                "structure":   "Use STAR: Situation→Task→Action→Result.",
                "impact":      "End with the outcome or metric.",
            }
            st.warning(f"**{weakest.upper()}** is your weakest area")
            st.info(tips[weakest])

            st.subheader("🕐 Recent sessions")
            for s in reversed(sessions[-4:]):
                avg = round(sum(s["avg_scores"].values())/5, 1)
                icon = "🟢" if avg>=4 else "🟡" if avg>=3 else "🔴"
                role_label = f" · {s.get('role','')}" if s.get('role') else ""
                st.caption(f"{icon} {s['date']}{role_label} — **{avg} / 5**")

# ══════════════════════════════════════════════════════════
# 🎤  PRACTICE
# ══════════════════════════════════════════════════════════
elif page == "🎤 Practice":
    st.markdown("""
    <div class="page-header">
        <h1>🎤 Practice Session</h1>
        <p>Answer AI-generated questions and get instant scored feedback</p>
    </div>""", unsafe_allow_html=True)

    for k,v in [("questions",[]),("current_q",0),("results",[]),("session_done",False),("show_eval",None),("practice_role","")]:
        if k not in st.session_state: st.session_state[k] = v

    if not st.session_state.questions and not st.session_state.session_done:
        st.markdown('<div class="glow-card">', unsafe_allow_html=True)
        with st.form("profile_form"):
            st.subheader("Set up your session")
            c1,c2 = st.columns(2)
            role  = c1.text_input("Role", placeholder="e.g. Data Analyst")
            level = c2.selectbox("Experience", ["Fresher","1-2 years","3-5 years"])
            c3,c4 = st.columns(2)
            focus = c3.selectbox("Focus", ["General","Behavioral","Technical","Situational"])
            count = c4.slider("Questions", 1, 10, 3)
            submitted = st.form_submit_button("Generate Questions 🚀")
        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            with st.spinner("Generating personalised questions..."):
                try:
                    qs = generate_questions(role, level, focus, count)
                    st.session_state.questions     = qs
                    st.session_state.practice_role = role
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    elif st.session_state.session_done:
        st.success("Session complete! 🎉")
        weakest = get_weakest_dim(uid)
        st.info(f"Focus next on: **{weakest.upper()}**")

        st.subheader("Session results")
        for i,r in enumerate(st.session_state.results, 1):
            with st.expander(f"Q{i}: {r['question'][:70]}..."):
                ev = r["evaluation"]
                cols = st.columns(5)
                for col,(dim,score) in zip(cols, ev["scores"].items()):
                    col.metric(dim.capitalize(), f"{score:.1f}")
                st.write(f"**Overall:** {ev['overall']:.1f}")
                if ev.get("strengths"):  st.success(f"✅ {ev['strengths'][0]}")
                if ev.get("weaknesses"): st.error(f"❌ {ev['weaknesses'][0]}")
                st.info(f"💡 {ev['tip']}")
                with st.expander("See ideal answer"):
                    st.write(ev.get("ideal_answer",""))

        if st.button("Start new session"):
            for k in ["questions","current_q","results","session_done","show_eval","practice_role"]:
                del st.session_state[k]
            st.rerun()

    else:
        qs=st.session_state.questions; idx=st.session_state.current_q; total=len(qs)
        st.progress(idx/total, text=f"Question {idx+1} of {total}")

        if idx < total:
            q = qs[idx]
            st.markdown(f"""
            <div class="glow-card">
                <span style="color:#a78bfa;font-size:12px;font-weight:600">{q['category'].upper()}</span>
                <p style="font-size:16px;color:#e5e7eb;margin:8px 0 0 0;font-weight:500">{q['question']}</p>
            </div>""", unsafe_allow_html=True)

            if st.session_state.show_eval:
                ev = st.session_state.show_eval
                st.divider()
                cols = st.columns(5)
                for col,(dim,score) in zip(cols, ev["scores"].items()):
                    col.metric(dim.capitalize(), f"{score:.1f}")
                st.metric("Overall", f"{ev['overall']:.1f}")
                if ev.get("strengths"):  st.success(f"✅ {ev['strengths'][0]}")
                if ev.get("weaknesses"): st.error(f"❌ {ev['weaknesses'][0]}")
                st.info(f"💡 {ev['tip']}")
                with st.expander("See ideal answer 👁"):
                    st.write(ev.get("ideal_answer",""))

                if idx+1 < total:
                    if st.button("Next question →"):
                        st.session_state.current_q += 1
                        st.session_state.show_eval  = None
                        st.rerun()
                else:
                    if st.button("Finish session ✅"):
                        avg = _average_scores(st.session_state.results)
                        save_session(
                            user_id    = uid,
                            role       = st.session_state.practice_role,
                            mode       = "practice",
                            avg_scores = avg,
                            results    = st.session_state.results
                        )
                        st.session_state.session_done = True
                        st.rerun()
            else:
                answer = st.text_area("Your answer", height=160, placeholder="Type your answer here...")
                if st.button("Submit answer →"):
                    if not answer.strip():
                        st.warning("Please type an answer first.")
                    else:
                        with st.spinner("Evaluating..."):
                            try:
                                ev = evaluate_answer(q["question"], q["category"], answer)
                                st.session_state.results.append({
                                    "question": q["question"],
                                    "answer":   answer,
                                    "evaluation": ev
                                })
                                st.session_state.show_eval = ev
                                st.rerun()
                            except Exception as e:
                                st.error(f"Evaluation error: {e}")

# ══════════════════════════════════════════════════════════
# 📈  PROGRESS
# ══════════════════════════════════════════════════════════
elif page == "📈 Progress":
    st.markdown("""
    <div class="page-header">
        <h1>📈 Progress Tracker</h1>
        <p>Track your improvement across sessions over time</p>
    </div>""", unsafe_allow_html=True)

    sessions = get_sessions(uid)

    if len(sessions) < 2:
        st.info("Complete at least 2 sessions to see your progress trends.")
    else:
        df = pd.DataFrame([
            {"date": s["date"], **{d: s["avg_scores"].get(d,0) for d in dims}}
            for s in sessions
        ])
        fig = px.line(df, x="date", y=dims, markers=True,
                      title="Score trends across sessions",
                      color_discrete_sequence=["#7c3aed","#10b981","#f59e0b","#3b82f6","#ef4444"])
        fig.update_layout(
            yaxis=dict(range=[0,5], gridcolor="#1f2937"),
            xaxis=dict(gridcolor="#1f2937"),
            height=360, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9ca3af"), legend=dict(bgcolor="rgba(0,0,0,0)"),
            title_font_color="#e5e7eb"
        )
        st.plotly_chart(fig, use_container_width=True)

        first = {d: sessions[0]["avg_scores"].get(d,0) for d in dims}
        last  = {d: sessions[-1]["avg_scores"].get(d,0) for d in dims}
        st.subheader("Improvement since first session")
        cols = st.columns(5)
        for col,d in zip(cols,dims):
            delta = round(last[d]-first[d], 2)
            col.metric(d.capitalize(), f"{last[d]:.1f}", f"{delta:+.2f}")

        st.divider()
        st.subheader("All sessions")
        for i,s in enumerate(reversed(sessions), 1):
            avg = round(sum(s["avg_scores"].values())/5, 1)
            icon = "🟢" if avg>=4 else "🟡" if avg>=3 else "🔴"
            role_label = f" · {s.get('role','')}" if s.get('role') else ""
            with st.expander(f"{icon} Session {len(sessions)-i+1} — {s['date']}{role_label} — {avg}/5"):
                cols = st.columns(5)
                for col,d in zip(cols,dims):
                    col.metric(d.capitalize(), f"{s['avg_scores'].get(d,0):.1f}")

# ══════════════════════════════════════════════════════════
# 📋  QUESTION BANK
# ══════════════════════════════════════════════════════════
elif page == "📋 Question Bank":
    st.markdown("""
    <div class="page-header">
        <h1>📋 Question Bank</h1>
        <p>Browse and study common interview questions by role and category</p>
    </div>""", unsafe_allow_html=True)

    BANK = {
        "Behavioral": [
            "Tell me about yourself.",
            "What is your greatest strength?",
            "What is your greatest weakness?",
            "Describe a challenge you overcame.",
            "Tell me about a time you worked in a team.",
            "Describe a time you led a project.",
            "Tell me about a time you disagreed with your manager.",
            "Give an example of a goal you reached and how you achieved it.",
            "Tell me about a time you failed. How did you handle it?",
            "How do you handle stress and pressure?",
        ],
        "Situational": [
            "Where do you see yourself in 5 years?",
            "Why do you want to leave your current job?",
            "Why do you want this role?",
            "How would you handle a difficult coworker?",
            "If you had too many tasks, what would you do?",
            "How would you handle constantly changing requirements?",
        ],
        "Data Analyst": [
            "What is data normalisation and when would you use it?",
            "Explain the difference between INNER JOIN and LEFT JOIN.",
            "What is the difference between supervised and unsupervised learning?",
            "How would you handle missing values in a dataset?",
            "What is a p-value and what does it tell you?",
            "Walk me through how you would approach a new dataset.",
            "What visualisation tools have you used and why?",
            "Explain overfitting and how to prevent it.",
        ],
        "Python Developer": [
            "What is the difference between a list and a tuple?",
            "Explain Python's GIL (Global Interpreter Lock).",
            "What are decorators in Python?",
            "How does garbage collection work in Python?",
            "What is the difference between deepcopy and copy?",
            "Explain list comprehension with an example.",
            "What are *args and **kwargs?",
        ],
        "HR / Final Round": [
            "Why should we hire you?",
            "What are your salary expectations?",
            "Do you have any questions for us?",
            "How soon can you start?",
            "What motivates you at work?",
            "How do you prioritise your work?",
            "Describe your ideal work environment.",
        ],
    }

    c1,c2 = st.columns([1,2])
    with c1:
        category = st.selectbox("Category", list(BANK.keys()))
        st.caption(f"{len(BANK[category])} questions")
        st.info("💡 Use STAR format for behavioral questions:\n\n**S**ituation → **T**ask → **A**ction → **R**esult")

    with c2:
        st.subheader(f"{category} questions")
        for i,q in enumerate(BANK[category], 1):
            st.markdown(f"""
            <div class="glow-card" style="padding:14px 18px;margin-bottom:8px">
                <span style="color:#a78bfa;font-size:11px;font-weight:600">Q{i}</span>
                <p style="color:#e5e7eb;margin:4px 0 0 0;font-size:14px">{q}</p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 📄  RESUME EVALUATOR
# ══════════════════════════════════════════════════════════
elif page == "📄 Resume Evaluator":
    st.markdown("""
    <div class="page-header">
        <h1>📄 Resume Evaluator</h1>
        <p>Upload your resume and get AI-powered feedback before your interview</p>
    </div>""", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.4])

    with col_left:
        st.subheader("Upload your resume")
        uploaded = st.file_uploader("PDF or TXT file", type=["pdf","txt"])
        role_re  = st.text_input("Target role", placeholder="e.g. Data Analyst")
        analyse  = st.button("Analyse Resume 🔍")

    with col_right:
        if analyse and uploaded and role_re:
            with st.spinner("Reading your resume..."):
                resume_text = read_resume(uploaded)

            if not resume_text.strip():
                st.error("Could not extract text. Try uploading a .txt version of your resume.")
            else:
                with st.spinner("AI is analysing your resume..."):
                    try:
                        groq_client = Groq(api_key=get_secret("GROQ_API_KEY"))
                        prompt = f"""You are an expert resume reviewer. Analyse this resume for a {role_re} role.
Resume: \"\"\"{resume_text}\"\"\"

Return ONLY valid JSON, no extra text:
{{
  "overall_score": <integer 1-10>,
  "impression": "2-3 sentence overall impression",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "issues": [
    {{"title": "Issue title", "severity": "High/Medium/Low", "fix": "How to fix it"}}
  ],
  "missing_sections": ["section1"],
  "ats_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "recommended_questions": [
    {{"category": "Technical", "question": "question based on actual resume content"}}
  ]
}}
Generate 3-5 issues, 4-6 ats_keywords, 3 recommended_questions from the actual resume."""

                        resp = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role":"user","content":prompt}],
                            temperature=0.3
                        )
                        raw = resp.choices[0].message.content.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"): raw = raw[4:]
                        data = json.loads(raw.strip())

                        score = data.get("overall_score", 5)
                        color = "#10b981" if score>=7 else "#f59e0b" if score>=5 else "#ef4444"
                        st.markdown(f"""
                        <div style="text-align:center;padding:20px;background:#1f2937;border-radius:12px;
                             margin-bottom:16px;border-left:4px solid {color}">
                            <div style="font-size:52px;font-weight:700;color:{color}">{score}
                                <span style="font-size:22px;color:#6b7280">/10</span>
                            </div>
                            <div style="color:#9ca3af;font-size:13px">Resume score for {role_re}</div>
                        </div>""", unsafe_allow_html=True)

                        st.subheader("Overall impression")
                        st.info(data.get("impression",""))

                        c1,c2 = st.columns(2)
                        with c1:
                            st.subheader("✅ Strengths")
                            for s in data.get("strengths",[]):
                                st.markdown(f"<div style='color:#10b981;padding:4px 0;font-size:13px'>✓ {s}</div>", unsafe_allow_html=True)
                        with c2:
                            st.subheader("⚠ Issues to fix")
                            sev_color = {"High":"#ef4444","Medium":"#f59e0b","Low":"#6b7280"}
                            for iss in data.get("issues",[]):
                                sev = iss.get("severity","Medium")
                                c = sev_color.get(sev,"#f59e0b")
                                st.markdown(f"""
                                <div style="border-left:3px solid {c};padding:8px 12px;margin-bottom:8px;
                                     background:#1f2937;border-radius:0 8px 8px 0">
                                    <div style="color:{c};font-size:11px;font-weight:600">{sev.upper()}</div>
                                    <div style="color:#e5e7eb;font-size:13px;font-weight:500">{iss.get('title','')}</div>
                                    <div style="color:#9ca3af;font-size:12px;margin-top:3px">Fix: {iss.get('fix','')}</div>
                                </div>""", unsafe_allow_html=True)

                        if data.get("missing_sections"):
                            st.subheader("❌ Missing sections")
                            st.warning("Consider adding: " + ", ".join(data["missing_sections"]))

                        st.subheader("🔑 ATS keywords to add")
                        kw_html = " ".join([
                            f'<span style="background:#1f2937;border:1px solid #7c3aed;color:#a78bfa;'
                            f'padding:4px 10px;border-radius:20px;font-size:12px;margin:3px;display:inline-block">{k}</span>'
                            for k in data.get("ats_keywords",[])
                        ])
                        st.markdown(kw_html, unsafe_allow_html=True)

                        st.subheader("🎯 Likely interview questions")
                        for q in data.get("recommended_questions",[]):
                            with st.expander(f"[{q.get('category','')}] {q.get('question','')}"):
                                st.caption("Practice this in the Interview Room or Practice page.")

                    except json.JSONDecodeError:
                        st.error("AI returned unexpected format. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif analyse:
            if not uploaded: st.warning("Please upload a resume file.")
            if not role_re:  st.warning("Please enter a target role.")
        else:
            st.markdown("""
            <div class="glow-card" style="text-align:center;padding:50px 20px">
                <div style="font-size:48px">📄</div>
                <div style="color:#9ca3af;margin-top:12px;font-size:14px">
                    Upload your resume and enter a target role<br>to get a full AI-powered analysis
                </div>
                <div style="margin-top:16px;color:#6b7280;font-size:12px">
                    Score /10 &nbsp;·&nbsp; Issues to fix &nbsp;·&nbsp; ATS keywords &nbsp;·&nbsp; Likely questions
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 🎥  INTERVIEW ROOM
# ══════════════════════════════════════════════════════════
elif page == "🎥 Interview Room":
    st.markdown("""
    <div class="page-header">
        <h1>🎥 AI Interview Room</h1>
        <p>Video-call style mock interview with AI interviewer Sarah Mitchell</p>
    </div>""", unsafe_allow_html=True)

    html_path = os.path.join(os.path.dirname(__file__), "interview_room.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    api_key = os.getenv("GROQ_API_KEY", "")
    html_content = html_content.replace(
        'id="inp-apikey" placeholder="gsk_..."',
        f'id="inp-apikey" placeholder="gsk_..." value="{api_key}"'
    )
    html_content = html_content.replace(
        '<label>Groq API key</label>',
        '<label style="display:none">Groq API key</label>'
    )
    html_content = html_content.replace(
        f'id="inp-apikey" placeholder="gsk_..." value="{api_key}"',
        f'id="inp-apikey" placeholder="gsk_..." value="{api_key}" style="display:none"'
    )
    st.components.v1.html(html_content, height=720, scrolling=False)