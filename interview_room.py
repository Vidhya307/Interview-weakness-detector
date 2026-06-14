import streamlit as st
import streamlit.components.v1 as components
from generator import generate_questions
from evaluator import evaluate_answer
from tracker import save_session

def show_interview_room():
    st.markdown("""
    <style>
    /* Hide default Streamlit padding for immersive look */
    .main .block-container { padding-top: 1rem; padding-bottom: 0; }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state init ──
    if "ir_questions"    not in st.session_state: st.session_state.ir_questions    = []
    if "ir_current"      not in st.session_state: st.session_state.ir_current      = 0
    if "ir_results"      not in st.session_state: st.session_state.ir_results      = []
    if "ir_phase"        not in st.session_state: st.session_state.ir_phase        = "setup"
    if "ir_evaluation"   not in st.session_state: st.session_state.ir_evaluation   = None
    if "ir_answer"       not in st.session_state: st.session_state.ir_answer       = ""

    phase = st.session_state.ir_phase

    # ════════════════════════════════
    # PHASE: SETUP
    # ════════════════════════════════
    if phase == "setup":
        _render_setup()

    # ════════════════════════════════
    # PHASE: INTERVIEW
    # ════════════════════════════════
    elif phase == "interview":
        _render_interview()

    # ════════════════════════════════
    # PHASE: RESULTS
    # ════════════════════════════════
    elif phase == "results":
        _render_results()


def _render_setup():
    # Video room UI with setup form embedded
    components.html(_setup_html(), height=620, scrolling=False)

    # Hidden form that Streamlit processes
    with st.form("ir_setup"):
        st.markdown("---")
        c1, c2 = st.columns(2)
        name  = c1.text_input("Your name", placeholder="e.g. Arun Kumar")
        role  = c2.text_input("Role", placeholder="e.g. Data Analyst")
        c3, c4, c5 = st.columns(3)
        level = c3.selectbox("Experience", ["Fresher","1-2 years","3-5 years","5+ years"])
        focus = c4.selectbox("Focus", ["General","Behavioral","Technical","Situational"])
        count = c5.slider("Questions", 1, 8, 3)
        go    = st.form_submit_button("🚀 Start Interview", use_container_width=True)

    if go:
        if not role:
            st.warning("Please enter the role you're applying for.")
            return
        with st.spinner("Sarah is preparing your questions..."):
            try:
                qs = generate_questions(role, level, focus, count)
                st.session_state.ir_questions  = qs
                st.session_state.ir_current    = 0
                st.session_state.ir_results    = []
                st.session_state.ir_phase      = "interview"
                st.session_state.ir_name       = name or "Candidate"
                st.session_state.ir_role       = role
                st.rerun()
            except Exception as e:
                st.error(f"Error generating questions: {e}")


def _render_interview():
    qs      = st.session_state.ir_questions
    idx     = st.session_state.ir_current
    total   = len(qs)
    name    = st.session_state.get("ir_name", "Candidate")

    if idx >= total:
        st.session_state.ir_phase = "results"
        st.rerun()
        return

    q = qs[idx]

    # ── Video call UI (avatar + question display) ──
    components.html(
        _interview_html(name, q["question"], q["category"], idx, total),
        height=420, scrolling=False
    )

    # ── Answer input below the video ──
    st.markdown(f"**Q{idx+1} [{q['category']}]:** {q['question']}")
    st.markdown("---")

    # Voice component — captures speech and fills text area
    components.html(_voice_capture_html(), height=80, scrolling=False)

    answer = st.text_area(
        "Your answer",
        value=st.session_state.ir_answer,
        height=130,
        placeholder="Speak using the mic above, or type your answer here...",
        key=f"answer_{idx}"
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    if col1.button("Submit & Evaluate →", use_container_width=True, type="primary"):
        if not answer.strip():
            st.warning("Please give an answer before submitting.")
            return
        with st.spinner("Sarah is evaluating your answer..."):
            try:
                ev = evaluate_answer(q["question"], q["category"], answer)
                st.session_state.ir_evaluation = ev
                st.session_state.ir_answer     = ""

                # Show evaluation inline
                _show_evaluation(ev, q["question"], answer)

                st.session_state.ir_results.append({
                    "question": q["question"],
                    "answer": answer,
                    "evaluation": ev
                })

                if idx + 1 < total:
                    if st.button("Next question →", use_container_width=True):
                        st.session_state.ir_current += 1
                        st.session_state.ir_evaluation = None
                        st.rerun()
                else:
                    if st.button("Finish & See Results ✅", use_container_width=True):
                        save_session(st.session_state.ir_results)
                        st.session_state.ir_phase = "results"
                        st.rerun()

            except Exception as e:
                st.error(f"Evaluation error: {e}")

    if col2.button("Skip →", use_container_width=True):
        st.session_state.ir_current += 1
        st.session_state.ir_answer  = ""
        st.rerun()

    if col3.button("End session", use_container_width=True):
        save_session(st.session_state.ir_results)
        st.session_state.ir_phase = "results"
        st.rerun()


def _show_evaluation(ev, question, answer):
    st.markdown("---")
    st.subheader("Sarah's feedback")

    cols = st.columns(5)
    for col, (dim, score) in zip(cols, ev["scores"].items()):
        color = "normal" if score >= 4 else "inverse"
        col.metric(dim.capitalize(), f"{score:.1f}", delta_color=color)

    st.metric("Overall", f"{ev['overall']:.1f} / 5")

    c1, c2 = st.columns(2)
    with c1:
        if ev.get("strengths"): st.success(f"✅ {ev['strengths'][0]}")
        if ev.get("weaknesses"): st.error(f"❌ {ev['weaknesses'][0]}")
    with c2:
        st.info(f"💡 {ev.get('tip','')}")

    with st.expander("See ideal answer"):
        st.write(ev.get("ideal_answer",""))

    # Speak feedback via browser TTS
    tip_text = ev.get("tip", "")
    overall  = ev.get("overall", 0)
    components.html(
        f"""<script>
        var u = new SpeechSynthesisUtterance("Your overall score is {overall:.1f}. {tip_text}");
        u.rate = 0.95; u.pitch = 1.1;
        var voices = speechSynthesis.getVoices();
        var v = voices.find(v => v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Google'));
        if(v) u.voice = v;
        speechSynthesis.speak(u);
        </script>""",
        height=0
    )


def _render_results():
    st.header("Interview Complete 🎉")
    results = st.session_state.ir_results

    if not results:
        st.info("No answers recorded.")
    else:
        scores  = [r["evaluation"]["overall"] for r in results]
        avg     = sum(scores) / len(scores)
        dims    = ["clarity","specificity","relevance","structure","impact"]
        dim_avg = {d: sum(r["evaluation"]["scores"][d] for r in results)/len(results) for d in dims}
        weakest = min(dim_avg, key=dim_avg.get)

        c1, c2, c3 = st.columns(3)
        c1.metric("Questions answered", len(results))
        c2.metric("Average score", f"{avg:.1f} / 5")
        c3.metric("Focus next on", weakest.capitalize())

        st.divider()

        for i, r in enumerate(results, 1):
            with st.expander(f"Q{i}: {r['question'][:70]}..."):
                ev = r["evaluation"]
                cols = st.columns(5)
                for col, (dim, score) in zip(cols, ev["scores"].items()):
                    col.metric(dim.capitalize(), f"{score:.1f}")
                st.write(f"**Tip:** {ev.get('tip','')}")
                with st.expander("Ideal answer"):
                    st.write(ev.get("ideal_answer",""))

    if st.button("Start new session", use_container_width=True):
        for key in ["ir_questions","ir_current","ir_results","ir_phase","ir_evaluation","ir_answer"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()


# ── HTML fragments ──────────────────────────────────────

def _setup_html():
    return """
    <div style="background:#0f1117;border-radius:12px;padding:24px;text-align:center;font-family:sans-serif">
      <div style="width:120px;height:120px;border-radius:50%;margin:0 auto 16px;background:#1a1d2e;border:2px solid #374151;overflow:hidden">
        <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
          <rect width="120" height="120" fill="#1a1d2e"/>
          <ellipse cx="60" cy="140" rx="50" ry="35" fill="#2a2d3a"/>
          <path d="M22 110 Q30 85 60 82 Q90 85 98 110 L110 120 L10 120 Z" fill="#374151"/>
          <path d="M44 82 Q60 90 60 102 Q50 96 42 98 Z" fill="#1f2937"/>
          <path d="M76 82 Q60 90 60 102 Q70 96 78 98 Z" fill="#1f2937"/>
          <path d="M52 85 Q60 81 68 85 L66 102 L60 105 L54 102 Z" fill="#e5e7eb"/>
          <rect x="54" y="71" width="12" height="15" rx="3" fill="#d4a87a"/>
          <ellipse cx="60" cy="57" rx="24" ry="27" fill="#d4a87a"/>
          <path d="M36 52 Q38 27 60 26 Q82 27 84 52 Q81 35 60 34 Q39 35 36 52 Z" fill="#1a0a00"/>
          <ellipse cx="36" cy="59" rx="4" ry="5" fill="#c9956e"/>
          <ellipse cx="84" cy="59" rx="4" ry="5" fill="#c9956e"/>
          <ellipse cx="50" cy="54" rx="5" ry="4" fill="#fff"/>
          <ellipse cx="70" cy="54" rx="5" ry="4" fill="#fff"/>
          <ellipse cx="51" cy="55" rx="3" ry="3" fill="#3b1f0a"/>
          <ellipse cx="71" cy="55" rx="3" ry="3" fill="#3b1f0a"/>
          <path d="M46 49 Q50 47 55 49" stroke="#3b1f0a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
          <path d="M65 49 Q70 47 74 49" stroke="#3b1f0a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
          <path d="M52 72 Q60 77 68 72" stroke="#b8825a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <div style="color:#e5e7eb;font-size:15px;font-weight:600">Sarah Mitchell</div>
      <div style="color:#6b7280;font-size:13px;margin-top:4px">Senior HR Manager · AI Interviewer</div>
      <div style="color:#9ca3af;font-size:13px;margin-top:16px;max-width:300px;margin-left:auto;margin-right:auto;line-height:1.6">
        Fill in the form below and click <strong style="color:#a78bfa">Start Interview</strong>.<br>
        Sarah will conduct your mock interview with voice.
      </div>
    </div>
    """


def _interview_html(name, question, category, idx, total):
    pct = int((idx / total) * 100)
    return f"""
    <div style="background:#0f1117;border-radius:12px;padding:20px;font-family:sans-serif;display:flex;align-items:center;gap:20px">
      <div style="position:relative;flex-shrink:0">
        <div id="av" style="width:100px;height:100px;border-radius:50%;border:2px solid #374151;overflow:hidden;background:#1a1d2e;transition:border-color 0.3s,box-shadow 0.3s">
          <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <rect width="120" height="120" fill="#1a1d2e"/>
            <path d="M22 110 Q30 85 60 82 Q90 85 98 110 L110 120 L10 120 Z" fill="#374151"/>
            <rect x="54" y="71" width="12" height="15" rx="3" fill="#d4a87a"/>
            <ellipse cx="60" cy="57" rx="24" ry="27" fill="#d4a87a"/>
            <path d="M36 52 Q38 27 60 26 Q82 27 84 52 Q81 35 60 34 Q39 35 36 52 Z" fill="#1a0a00"/>
            <ellipse cx="50" cy="54" rx="5" ry="4" fill="#fff"/>
            <ellipse cx="70" cy="54" rx="5" ry="4" fill="#fff"/>
            <ellipse cx="51" cy="55" rx="3" ry="3" fill="#3b1f0a"/>
            <ellipse cx="71" cy="55" rx="3" ry="3" fill="#3b1f0a"/>
            <path d="M52 72 Q60 77 68 72" stroke="#b8825a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
          </svg>
        </div>
        <div id="wave" style="display:flex;align-items:center;gap:3px;height:18px;margin-top:8px;justify-content:center;opacity:0;transition:opacity 0.3s">
          <span style="display:block;width:3px;background:#a78bfa;border-radius:2px;height:6px;animation:w 0.8s ease-in-out infinite 0s"></span>
          <span style="display:block;width:3px;background:#a78bfa;border-radius:2px;height:14px;animation:w 0.8s ease-in-out infinite 0.1s"></span>
          <span style="display:block;width:3px;background:#a78bfa;border-radius:2px;height:18px;animation:w 0.8s ease-in-out infinite 0.2s"></span>
          <span style="display:block;width:3px;background:#a78bfa;border-radius:2px;height:14px;animation:w 0.8s ease-in-out infinite 0.3s"></span>
          <span style="display:block;width:3px;background:#a78bfa;border-radius:2px;height:6px;animation:w 0.8s ease-in-out infinite 0.4s"></span>
        </div>
      </div>
      <div style="flex:1">
        <div style="color:#6b7280;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px">Sarah Mitchell · Question {idx+1} of {total}</div>
        <div style="color:#e5e7eb;font-size:15px;line-height:1.6;margin-bottom:12px">{question}</div>
        <div style="background:#1f2330;border-radius:4px;height:4px;overflow:hidden">
          <div style="width:{pct}%;height:100%;background:#7c3aed;border-radius:4px;transition:width 0.4s"></div>
        </div>
        <div style="color:#6b7280;font-size:11px;margin-top:5px">{category} · {pct}% complete</div>
      </div>
    </div>
    <style>
    @keyframes w {{ 0%,100%{{transform:scaleY(0.4)}} 50%{{transform:scaleY(1)}} }}
    </style>
    <script>
    var av = document.getElementById('av');
    var wave = document.getElementById('wave');
    var text = "{question}";
    var u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95; u.pitch = 1.1;
    speechSynthesis.getVoices();
    setTimeout(function() {{
      var voices = speechSynthesis.getVoices();
      var v = voices.find(function(v) {{ return v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Karen') || (v.lang==='en-US' && v.name.toLowerCase().includes('google')); }});
      if(v) u.voice = v;
      u.onstart = function() {{ av.style.borderColor='#a78bfa'; av.style.boxShadow='0 0 0 6px rgba(167,139,250,0.15)'; wave.style.opacity='1'; }};
      u.onend   = function() {{ av.style.borderColor='#374151'; av.style.boxShadow='none'; wave.style.opacity='0'; }};
      speechSynthesis.speak(u);
    }}, 400);
    </script>
    """


def _voice_capture_html():
    return """
    <div style="display:flex;align-items:center;gap:12px;padding:8px 0;font-family:sans-serif">
      <button id="micBtn" onclick="toggleMic()" style="width:44px;height:44px;border-radius:50%;background:#1f2330;border:1px solid #374151;color:#e5e7eb;font-size:20px;cursor:pointer;transition:all 0.2s;flex-shrink:0">🎤</button>
      <div id="micStatus" style="font-size:13px;color:#6b7280">Click mic to record your answer, click again to stop</div>
      <div id="micWave" style="display:flex;align-items:center;gap:3px;opacity:0;transition:opacity 0.3s">
        <span style="display:block;width:3px;background:#10b981;border-radius:2px;height:6px;animation:w2 0.6s ease-in-out infinite 0s"></span>
        <span style="display:block;width:3px;background:#10b981;border-radius:2px;height:14px;animation:w2 0.6s ease-in-out infinite 0.1s"></span>
        <span style="display:block;width:3px;background:#10b981;border-radius:2px;height:18px;animation:w2 0.6s ease-in-out infinite 0.15s"></span>
        <span style="display:block;width:3px;background:#10b981;border-radius:2px;height:14px;animation:w2 0.6s ease-in-out infinite 0.2s"></span>
        <span style="display:block;width:3px;background:#10b981;border-radius:2px;height:6px;animation:w2 0.6s ease-in-out infinite 0.3s"></span>
      </div>
    </div>
    <style>@keyframes w2{0%,100%{transform:scaleY(0.4)}50%{transform:scaleY(1)}}</style>
    <script>
    var recog = null; var listening = false;
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    function toggleMic() {
      if (!SR) { document.getElementById('micStatus').textContent = 'Voice not supported — use Chrome'; return; }
      if (listening) {
        recog.stop(); listening = false;
        document.getElementById('micBtn').style.background = '#1f2330';
        document.getElementById('micBtn').textContent = '🎤';
        document.getElementById('micWave').style.opacity = '0';
        document.getElementById('micStatus').textContent = 'Recording stopped — your answer is in the text box above';
      } else {
        recog = new SR(); recog.continuous = true; recog.interimResults = true; recog.lang = 'en-US';
        recog.onresult = function(e) {
          var t = '';
          for (var i = 0; i < e.results.length; i++) t += e.results[i][0].transcript;
          var areas = window.parent.document.querySelectorAll('textarea');
          areas.forEach(function(a) { if(a.offsetParent !== null) { a.value = t; a.dispatchEvent(new Event('input', {bubbles:true})); }});
        };
        recog.start(); listening = true;
        document.getElementById('micBtn').style.background = '#10b981';
        document.getElementById('micBtn').textContent = '⏹';
        document.getElementById('micWave').style.opacity = '1';
        document.getElementById('micStatus').textContent = 'Listening... click stop when done';
      }
    }
    </script>
    """