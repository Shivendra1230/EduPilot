import os
import re
import uuid
import requests
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()
BACKEND = os.getenv("BACKEND_URL", "https://edupilot-backend-2iae.onrender.com").rstrip("/")

# Each Streamlit session gets its own workspace.
# This prevents old "demo" data from appearing in a fresh run.
if "user_id" not in st.session_state:
    st.session_state["user_id"] = f"student_{uuid.uuid4().hex[:12]}"

USER_ID = st.session_state["user_id"]

st.set_page_config(
    page_title="EduPilot | Adaptive AI Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Theme ----------------
st.markdown(
    """
<style>
:root{--bg:#090b10;--panel:#11141b;--panel2:#161a22;--line:#252a35;--text:#f5f7fb;--muted:#8f97a8;--accent:#ff4f67;--violet:#8b5cf6;--green:#38d39f;--yellow:#f4c95d;--red:#ff6478;}
.stApp{background:var(--bg);color:var(--text)}
.block-container{max-width:1440px;padding:1.2rem 2.3rem 3.5rem}
[data-testid="stHeader"]{background:rgba(9,11,16,.86)}
[data-testid="stSidebar"]{background:#0d1016;border-right:1px solid var(--line)}
#MainMenu,footer{visibility:hidden}
.brand{display:flex;align-items:center;gap:12px;margin:3px 0 0}.brand-icon{font-size:39px}.brand-name{font-size:2.25rem;font-weight:850;letter-spacing:-1.4px}.brand-sub{color:var(--muted);margin:0 0 1.1rem 52px;font-size:.95rem}
.section-title{font-size:1.48rem;font-weight:820;letter-spacing:-.5px;margin:1rem 0 .25rem}.section-sub{color:var(--muted);font-size:.88rem;margin-bottom:1rem}
.hero{background:linear-gradient(135deg,#151923 0%,#11141b 55%,#18131b 100%);border:1px solid var(--line);border-radius:22px;padding:23px 25px;margin:5px 0 18px;box-shadow:0 18px 55px rgba(0,0,0,.18)}
.hero-kicker{color:#bcaeff;font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:1.5px}.hero-title{font-size:1.72rem;font-weight:820;margin:5px 0}.hero-text{color:var(--muted);font-size:.91rem;max-width:850px}
.metric-card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px 17px;min-height:108px}.metric-label{color:var(--muted);font-size:.76rem;font-weight:700;text-transform:uppercase;letter-spacing:.4px}.metric-value{font-size:1.9rem;font-weight:850;margin-top:6px;letter-spacing:-1px}.metric-note{color:#737b8b;font-size:.73rem;margin-top:2px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:17px;padding:18px 19px;margin-bottom:15px}.panel-title{font-size:1rem;font-weight:800}.panel-sub{color:var(--muted);font-size:.77rem;margin-top:3px;margin-bottom:12px}
.topic-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid #20242d}.topic-row:last-child{border-bottom:0}.topic-name{font-weight:650;font-size:.86rem}.topic-score{color:#cbd0da;font-size:.79rem;font-weight:750}.badge{border-radius:999px;padding:4px 9px;font-size:.66rem;font-weight:800}.badge-green{background:rgba(56,211,159,.12);color:var(--green)}.badge-yellow{background:rgba(244,201,93,.12);color:var(--yellow)}.badge-red{background:rgba(255,100,120,.12);color:var(--red)}.badge-gray{background:#20242d;color:#9ba3b2}
.focus-card{background:linear-gradient(135deg,rgba(139,92,246,.13),rgba(255,79,103,.07));border:1px solid #332c4d;border-radius:15px;padding:15px}.focus-label{color:#bcaeff;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:1px}.focus-topic{font-size:1.08rem;font-weight:800;margin:4px 0}.focus-reason{color:var(--muted);font-size:.78rem}
.video-hero{background:linear-gradient(135deg,#141821,#11131a);border:1px solid #2b3040;border-radius:20px;padding:21px;margin-bottom:16px}.video-badge{display:inline-block;border:1px solid #3a4050;background:#191d27;border-radius:999px;padding:5px 10px;color:#bdb4ff;font-size:.68rem;font-weight:800}.video-title{font-size:1.5rem;font-weight:820;margin:9px 0 3px}.video-meta{color:var(--muted);font-size:.8rem}
.quick{border:1px solid var(--line);background:#13161e;border-radius:13px;padding:12px 13px;min-height:74px}.quick-title{font-size:.84rem;font-weight:800}.quick-text{font-size:.72rem;color:var(--muted);margin-top:3px}
.empty-state{text-align:center;padding:45px 20px;color:var(--muted)}.empty-icon{font-size:2.3rem;margin-bottom:7px}.small-muted{color:var(--muted);font-size:.76rem}
button[data-baseweb="tab"]{font-weight:750!important;color:#9fa7b7!important}button[data-baseweb="tab"][aria-selected="true"]{color:#fff!important}div[data-baseweb="tab-highlight"]{background:var(--accent)!important}
.stButton>button,.stDownloadButton>button{border-radius:10px;border:1px solid #343a48;background:#151821;color:#f6f7fa;font-weight:720}.stButton>button:hover{border-color:#626a7c;color:#fff}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#ff4f67,#d93d55);border-color:#ff4f67}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div{background:#151821!important;border-color:#303644!important;border-radius:10px!important}.stTextInput input,textarea{color:#fff!important}
[data-testid="stFileUploaderDropzone"]{background:#141720;border:1px dashed #3a4050;border-radius:13px}
.stProgress>div>div{background:linear-gradient(90deg,var(--violet),var(--accent))}
/* YouTube Learning Lab */
.yt-shell{background:linear-gradient(145deg,#121722 0%,#0f131b 58%,#171225 100%);border:1px solid #2a3040;border-radius:24px;padding:24px;margin:4px 0 18px;box-shadow:0 18px 55px rgba(0,0,0,.16)}
.yt-kicker{display:flex;align-items:center;gap:8px;color:#bcaeff;font-size:.68rem;font-weight:850;text-transform:uppercase;letter-spacing:1.3px}
.yt-title{font-size:1.72rem;font-weight:850;letter-spacing:-.7px;margin:7px 0 5px}.yt-desc{color:var(--muted);font-size:.86rem;max-width:850px;line-height:1.55}
.yt-flow{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.yt-step{border:1px solid #303747;background:#151a24;border-radius:999px;padding:6px 10px;color:#cbd1dc;font-size:.68rem;font-weight:750}.yt-step b{color:#fff}
.yt-stat{background:#121720;border:1px solid #292f3c;border-radius:14px;padding:13px 14px}.yt-stat-label{color:#7f8899;font-size:.64rem;text-transform:uppercase;letter-spacing:.7px;font-weight:800}.yt-stat-value{font-size:1.15rem;font-weight:850;margin-top:4px}.yt-stat-note{font-size:.68rem;color:#737d8e;margin-top:2px}
.yt-section{font-size:1.12rem;font-weight:830;margin:19px 0 4px}.yt-section-sub{font-size:.76rem;color:var(--muted);margin-bottom:11px}
.transcript-box{background:#0d1118;border:1px solid #292f3b;border-radius:15px;max-height:430px;overflow:auto;padding:5px 14px}
.transcript-line{padding:11px 4px;border-bottom:1px solid #202530;line-height:1.5;font-size:.79rem;color:#d4d8e0}.transcript-line:last-child{border-bottom:0}.timestamp{display:inline-block;color:#bcaeff;background:#211d32;border:1px solid #37304e;border-radius:6px;padding:2px 6px;margin-right:8px;font-size:.65rem;font-weight:800}
.map-card{position:relative;background:linear-gradient(145deg,#151a24,#11151d);border:1px solid #2a3040;border-radius:15px;padding:15px 15px 16px;min-height:108px;margin-bottom:12px}
.map-num{display:inline-flex;width:26px;height:26px;border-radius:8px;align-items:center;justify-content:center;background:#27213b;color:#c9beff;font-size:.68rem;font-weight:850}.map-name{font-size:.84rem;font-weight:800;margin:9px 0 4px}.map-meta{color:#778193;font-size:.68rem;line-height:1.45}
.ai-chip{display:inline-flex;align-items:center;gap:5px;border:1px solid #3a3152;background:#211c2f;color:#c9beff;border-radius:999px;padding:5px 9px;font-size:.63rem;font-weight:800}
.source-chip{display:inline-flex;align-items:center;gap:5px;border:1px solid #293844;background:#151e22;color:#91d8c0;border-radius:999px;padding:5px 9px;font-size:.63rem;font-weight:800}
/* Final responsive + overflow protection */
.stApp{
    width:100% !important;
    max-width:100vw !important;
    overflow-x:hidden !important;
}

.block-container{
    width:100% !important;
    max-width:1440px !important;
    margin:0 auto !important;
    box-sizing:border-box !important;
    overflow-x:hidden !important;
}

[data-testid="stHorizontalBlock"]{
    width:100% !important;
    max-width:100% !important;
    box-sizing:border-box !important;
}

[data-testid="stColumn"]{
    min-width:0 !important;
    max-width:100% !important;
    box-sizing:border-box !important;
}

.metric-card,
.panel,
.hero,
.yt-shell,
.yt-stat,
.video-hero,
.quick,
.focus-card,
.transcript-box,
.map-card{
    max-width:100% !important;
    box-sizing:border-box !important;
}

@media(max-width:900px){
    .block-container{
        width:100% !important;
        max-width:100% !important;
        padding:1rem !important;
    }

    .brand-name{
        font-size:2rem;
    }

    .brand-sub{
        margin-left:50px;
    }
}

@media(max-width:700px){
    .block-container{
        padding:.7rem !important;
    }

    .brand{
        max-width:100% !important;
        flex-wrap:wrap !important;
    }

    .brand-name{
        font-size:1.7rem;
    }

    .brand-sub{
        margin-left:0;
        font-size:.8rem;
        max-width:100% !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path, timeout=30):
    try:
        return requests.get(f"{BACKEND}{path}", timeout=timeout)
    except requests.RequestException:
        return None


def api_post(path, **kwargs):
    try:
        return requests.post(f"{BACKEND}{path}", timeout=kwargs.pop("timeout", 30), **kwargs)
    except requests.RequestException:
        return None


def error_text(response):
    if response is None:
        return "Backend is not reachable. Please check the deployed EduPilot API."
    try:
        return response.json().get("detail", response.text)
    except Exception:
        return response.text or "Request failed."


def load_topics(force=False):
    if not force and "topics" in st.session_state:
        return st.session_state["topics"]
    r = api_get(f"/progress/topics/{USER_ID}")
    topics = r.json() if r is not None and r.ok else []
    st.session_state["topics"] = topics
    return topics


def status_badge(status):
    mapping = {"strong": ("Strong", "badge-green"), "revision": ("Revision", "badge-yellow"), "weak": ("Weak", "badge-red"), "unknown": ("Not assessed", "badge-gray")}
    label, css = mapping.get(status, ("Not assessed", "badge-gray"))
    return f'<span class="badge {css}">{label}</span>'


# ---------------- Header ----------------
st.markdown('<div class="brand"><div class="brand-icon">🎓</div><div class="brand-name">EduPilot</div></div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Adaptive AI Learning Copilot · Learn from notes, PDFs and YouTube lectures</div>', unsafe_allow_html=True)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("### 📚 Study Material")
    st.caption("Build a personal learning context from your notes, syllabus and PYQs.")
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    doc_type = st.selectbox("Material type", ["notes", "syllabus", "pyq"], format_func=lambda x: x.title())
    if uploaded:
        st.caption(f"Selected: **{uploaded.name}**")
    if uploaded and st.button("Process Material", use_container_width=True, type="primary"):
        with st.spinner("Processing and indexing your material..."):
            r = api_post("/upload", files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}, data={"user_id": USER_ID, "document_type": doc_type}, timeout=180)
        if r is not None and r.ok:
            st.success(f"Added {r.json().get('chunks_added', 0)} chunks")
            st.session_state.pop("topics", None)
        else:
            st.error(error_text(r))
    st.divider()

    if st.button("🆕 New Learning Workspace", use_container_width=True):
        # Start a new isolated workspace without deleting old data.
        st.session_state.clear()
        st.session_state["user_id"] = f"student_{uuid.uuid4().hex[:12]}"
        st.rerun()

    st.caption("Start fresh anytime. Previous workspace data is kept separate.")

    st.divider()
    st.markdown("#### Workflow")
    st.markdown("**1** Upload material\n\n**2** Add a YouTube lecture\n\n**3** Ask AI / take quizzes\n\n**4** Follow your adaptive plan")
    st.divider()
    st.caption("EduPilot · Production-style MVP")

# ---------------- Navigation ----------------
tabs = st.tabs(["📊 Dashboard", "🤖 AI Tutor", "🎥 Video Learning", "📝 Adaptive Quiz", "🎯 Study Plan"])

# ---------------- Dashboard ----------------
with tabs[0]:
    topics = load_topics()
    assessed = [t for t in topics if t.get("status") != "unknown"]
    strong = [t for t in topics if t.get("status") == "strong"]
    revision = [t for t in topics if t.get("status") == "revision"]
    weak = [t for t in topics if t.get("status") == "weak"]
    avg_score = round(sum(float(t.get("score", 0)) for t in assessed) / len(assessed)) if assessed else 0

    st.markdown('<div class="hero"><div class="hero-kicker">Personalized learning</div><div class="hero-title">Know what to study next.</div><div class="hero-text">EduPilot combines your study material, lecture transcripts and quiz performance into one adaptive learning workspace.</div></div>', unsafe_allow_html=True)
    cards=[("Topics",len(topics),"from indexed material"),("Mastery",f"{avg_score}%","assessed average" if assessed else "not assessed yet"),("Strong",len(strong),"75% or higher"),("Needs Focus",len(weak)+len(revision),"weak + revision")]

    metric_row_1 = st.columns(2, gap="medium")
    for col,(label,value,note) in zip(metric_row_1,cards[:2]):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
                unsafe_allow_html=True
            )

    st.write("")

    metric_row_2 = st.columns(2, gap="medium")
    for col,(label,value,note) in zip(metric_row_2,cards[2:]):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-title">Learning overview</div><div class="section-sub">See where you are strong, where you need revision, and what to focus on next.</div>',unsafe_allow_html=True)
    if st.button("↻ Extract / Refresh Topics"):
        with st.spinner("Analyzing your indexed material..."):
            r=api_post("/progress/topics",json={"user_id":USER_ID},timeout=180)
        if r is not None and r.ok:
            st.session_state["topics"]=r.json(); st.rerun()
        else: st.error(error_text(r))

    if not topics:
        st.markdown('<div class="panel empty-state"><div class="empty-icon">📄</div><b>No learning profile yet</b><br>Upload a PDF from the sidebar or process a YouTube lecture.</div>',unsafe_allow_html=True)
    else:
        left,right=st.columns([1.3,.85])
        with left:
            chart_topics=sorted(topics,key=lambda x:float(x.get("score",0)),reverse=True)[:15]
            chart_data=[{"Topic":t["name"][:38],"Score":float(t.get("score",0))} for t in chart_topics]
            fig=px.bar(chart_data,x="Score",y="Topic",orientation="h",range_x=[0,100])
            fig.update_traces(marker_color="#8b5cf6",hovertemplate="%{y}<br>Mastery: %{x:.0f}%<extra></extra>")
            fig.update_layout(height=max(410,26*len(chart_data)+100),margin=dict(l=0,r=10,t=40,b=5),paper_bgcolor="#11141b",plot_bgcolor="#11141b",font_color="#cdd2dc",xaxis_title=None,yaxis_title=None)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        with right:
            focus=weak[0] if weak else revision[0] if revision else (topics[0] if topics else None)
            if focus:
                reason="Your lowest assessed score." if focus in weak else "This topic needs revision." if focus in revision else "Start a quiz to measure mastery."
                st.markdown(f'<div class="focus-card"><div class="focus-label">Recommended focus</div><div class="focus-topic">{focus["name"]}</div><div class="focus-reason">{reason}</div></div>',unsafe_allow_html=True)
            st.markdown('<div class="panel"><div class="panel-title">Profile snapshot</div><div class="panel-sub">Current mastery distribution</div>',unsafe_allow_html=True)
            for label,items,cls in [("Strong",strong,"badge-green"),("Revision",revision,"badge-yellow"),("Weak",weak,"badge-red")]:
                st.markdown(f'<div class="topic-row"><span class="topic-name">{label}</span><span class="badge {cls}">{len(items)}</span></div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)

        s1,s2,s3=st.columns(3)
        for col,title,subtitle,items,empty,cls in [
            (s1,"🟢 Strong Topics","75%+",strong,"No strong topics yet.","badge-green"),
            (s2,"🟡 Needs Revision","50–74%",revision,"No revision topics yet.","badge-yellow"),
            (s3,"🔴 Weak Topics","Below 50%",weak,"No weak topics yet.","badge-red"),
        ]:
            with col:
                st.markdown(f'<div class="panel"><div class="panel-title">{title}</div><div class="panel-sub">{subtitle}</div>',unsafe_allow_html=True)
                if items:
                    for t in sorted(items,key=lambda x:float(x.get("score",0)))[:7]:
                        st.markdown(f'<div class="topic-row"><span class="topic-name">{t["name"]}</span><span class="topic-score">{float(t.get("score",0)):.0f}%</span></div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="empty-state" style="padding:18px 3px">{empty}<br><span class="small-muted">Take a quiz to update mastery.</span></div>',unsafe_allow_html=True)
                st.markdown('</div>',unsafe_allow_html=True)

# ---------------- AI Tutor ----------------
with tabs[1]:
    st.markdown('<div class="section-title">AI Tutor</div><div class="section-sub">Ask questions grounded in your uploaded study material.</div>',unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages=[]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    question=st.chat_input("Ask something from your notes...")
    if question:
        st.session_state.messages.append({"role":"user","content":question})
        with st.chat_message("user"): st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching your material..."):
                r=api_post("/chat",json={"user_id":USER_ID,"question":question},timeout=180)
            if r is not None and r.ok:
                answer=r.json().get("answer","No answer returned."); st.markdown(answer); st.session_state.messages.append({"role":"assistant","content":answer})
            else: st.error(error_text(r))

# ---------------- YouTube Learning ----------------
with tabs[2]:
    st.markdown(
        '<div class="yt-shell">'
        '<div class="yt-kicker">🎥 YouTube Learning Lab · Lecture Intelligence</div>'
        '<div class="yt-title">Turn one lecture into a study workspace.</div>'
        '<div class="yt-desc">Fetch the original YouTube captions, index them for search, then use Groq to build an AI learning map from the transcript. The transcript itself is not AI-generated.</div>'
        '<div class="yt-flow">'
        '<span class="yt-step"><b>01</b> Captions</span><span class="yt-step"><b>02</b> Searchable transcript</span>'
        '<span class="yt-step"><b>03</b> AI topic map</span><span class="yt-step"><b>04</b> Tutor + Quiz</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    with st.container():
        c_url, c_lang, c_action = st.columns([2.45, 1.0, 1.0])
        with c_url:
            url = st.text_input(
                "YouTube URL",
                placeholder="Paste a lecture link · https://youtube.com/watch?v=...",
                key="yt_url",
                label_visibility="collapsed",
            )
        with c_lang:
            lang = st.selectbox(
                "Answer language",
                ["English", "Hindi", "Hinglish"],
                index=0,
                key="yt_lang",
                label_visibility="collapsed",
            )
        with c_action:
            process_clicked = st.button("⚡ Process Lecture", type="primary", use_container_width=True)

    if process_clicked:
        if not url.strip():
            st.warning("Paste a YouTube URL first.")
        else:
            status = st.status("Building your lecture workspace...", expanded=True)
            try:
                status.write("🎙 Fetching available YouTube captions...")
                r = api_post(
                    "/youtube/process",
                    json={"user_id": USER_ID, "url": url.strip()},
                    timeout=180,
                )
                if r is None or not r.ok:
                    status.update(label="Transcript could not be loaded", state="error", expanded=False)
                    st.error(error_text(r))
                else:
                    meta = r.json()
                    st.session_state.video = meta
                    st.session_state.video_topics = []
                    st.session_state.video_summary = ""
                    st.session_state.video_answer = ""
                    st.session_state.video_quiz = []
                    status.write(f"✓ {meta.get('snippet_count', 0)} caption lines fetched.")
                    status.write(f"✓ {meta.get('chunk_count', 0)} searchable transcript chunks created.")
                    status.write("🧠 Generating the learning map from the transcript...")
                    tr = api_post(
                        "/youtube/topics",
                        json={"user_id": USER_ID, "video_id": meta["video_id"]},
                        timeout=180,
                    )
                    if tr is not None and tr.ok:
                        st.session_state.video_topics = tr.json().get("topics", [])
                    else:
                        st.session_state.video_topics = []
                        st.warning(error_text(tr))
                    tx = api_get(
                        f"/youtube/{USER_ID}/{meta['video_id']}/transcript",
                        timeout=60,
                    )
                    if tx is not None and tx.ok:
                        st.session_state.video_transcript = tx.json().get("chunks", [])
                    else:
                        st.session_state.video_transcript = []
                    status.update(label="Lecture workspace ready", state="complete", expanded=False)
                    st.rerun()
            except Exception as exc:
                status.update(label="Something went wrong", state="error", expanded=False)
                st.error(str(exc))

    video = st.session_state.get("video")
    if not video:
        st.markdown(
            '<div class="panel empty-state">'
            '<div class="empty-icon">🎬</div>'
            '<b>Paste a lecture URL to get started</b><br>'
            '<span class="small-muted">EduPilot will use YouTube captions as the source, then build an AI-powered topic map from that transcript.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        topics_video = st.session_state.get("video_topics", [])
        transcript_chunks = st.session_state.get("video_transcript", [])

        st.markdown(
            f'<div class="yt-shell" style="padding:18px 20px">'
            f'<div class="yt-kicker"><span class="source-chip">● CAPTIONS INDEXED</span> '
            f'<span class="ai-chip">✦ AI MAP READY</span></div>'
            f'<div class="video-title">{video.get("title","YouTube lecture")}</div>'
            f'<div class="video-meta">{video.get("language","Unknown")} captions · '
            f'{"Auto-generated" if video.get("is_generated") else "Creator-provided"} · '
            f'{video.get("snippet_count",0)} caption lines · {video.get("chunk_count",0)} searchable chunks</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        s1, s2, s3, s4 = st.columns(4)
        s1.markdown(
            f'<div class="yt-stat"><div class="yt-stat-label">Caption source</div>'
            f'<div class="yt-stat-value">YouTube</div><div class="yt-stat-note">Original captions</div></div>',
            unsafe_allow_html=True,
        )
        s2.markdown(
            f'<div class="yt-stat"><div class="yt-stat-label">Transcript</div>'
            f'<div class="yt-stat-value">{len(transcript_chunks)}</div><div class="yt-stat-note">indexed chunks</div></div>',
            unsafe_allow_html=True,
        )
        s3.markdown(
            f'<div class="yt-stat"><div class="yt-stat-label">Learning map</div>'
            f'<div class="yt-stat-value">{len(topics_video)}</div><div class="yt-stat-note">AI concepts</div></div>',
            unsafe_allow_html=True,
        )
        s4.markdown(
            f'<div class="yt-stat"><div class="yt-stat-label">Language</div>'
            f'<div class="yt-stat-value">{video.get("language_code","--").upper()}</div><div class="yt-stat-note">caption language</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="yt-section">Lecture & transcript</div>'
                    '<div class="yt-section-sub">Read the actual caption text and search inside it. Timestamps are preserved from YouTube.</div>',
                    unsafe_allow_html=True)
        left, right = st.columns([1.02, 0.98], gap="large")
        with left:
            st.video(video.get("url"))
        with right:
            transcript_query = st.text_input(
                "Search transcript",
                placeholder="Search a concept, keyword or phrase...",
                key="transcript_search",
            )
            visible = transcript_chunks
            if transcript_query.strip():
                needle = transcript_query.strip().lower()
                visible = [c for c in transcript_chunks if needle in c.lower()]
            if not transcript_chunks:
                st.info("Transcript text is not available in the workspace.")
            else:
                st.caption(f"Showing {len(visible)} of {len(transcript_chunks)} transcript chunks")
                html = '<div class="transcript-box">'
                for chunk in visible:
                    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", chunk, re.S)
                    if m:
                        html += f'<div class="transcript-line"><span class="timestamp">{m.group(1)}</span>{m.group(2)}</div>'
                    else:
                        html += f'<div class="transcript-line">{chunk}</div>'
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        st.markdown('<div class="yt-section">AI learning map</div>'
                    '<div class="yt-section-sub">Concepts are extracted by Groq from the indexed transcript — no topic is intentionally taken from outside the lecture.</div>',
                    unsafe_allow_html=True)
        map_left, map_right = st.columns([2.0, 0.7], gap="large")
        with map_right:
            if st.button("↻ Regenerate map", use_container_width=True):
                with st.spinner("Rebuilding the map from the full transcript..."):
                    r = api_post(
                        "/youtube/topics",
                        json={"user_id": USER_ID, "video_id": video["video_id"]},
                        timeout=180,
                    )
                if r is not None and r.ok:
                    st.session_state.video_topics = r.json().get("topics", [])
                    if st.session_state.video_topics:
                        st.success(f"{len(st.session_state.video_topics)} concepts found.")
                    else:
                        st.warning("No clear learning topics were found.")
                    st.rerun()
                else:
                    st.error(error_text(r))
            st.markdown(
                '<div class="panel" style="margin-top:10px">'
                '<div class="panel-title">How this works</div>'
                '<div class="panel-sub">Transcript → full-text context → structured AI topic extraction</div>'
                '<span class="source-chip">● SOURCE: YOUTUBE CAPTIONS</span><br><br>'
                '<span class="ai-chip">✦ MAP: GROQ AI</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with map_left:
            if topics_video:
                cols = st.columns(3)
                for i, topic in enumerate(topics_video):
                    cols[i % 3].markdown(
                        f'<div class="map-card"><span class="map-num">{i+1:02d}</span>'
                        f'<div class="map-name">{topic}</div>'
                        f'<div class="map-meta">Concept identified from this lecture</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="panel empty-state" style="padding:28px">'
                    '<div class="empty-icon">🧩</div><b>No learning map yet</b><br>'
                    '<span class="small-muted">Click “Regenerate map” to analyze the full transcript.</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="yt-section">Ask this lecture</div>'
                    '<div class="yt-section-sub">Questions are answered from retrieved transcript evidence only.</div>',
                    unsafe_allow_html=True)
        vq = st.text_input(
            "Your question",
            placeholder="Explain this concept in simple Hinglish...",
            key="video_question",
            label_visibility="collapsed",
        )
        if st.button("Ask Video AI", type="primary"):
            if not vq.strip():
                st.warning("Enter a question first.")
            else:
                with st.spinner("Searching the lecture and composing the answer..."):
                    r = api_post(
                        "/youtube/chat",
                        json={
                            "user_id": USER_ID,
                            "video_id": video["video_id"],
                            "question": vq.strip(),
                            "language": lang,
                        },
                        timeout=180,
                    )
                if r is not None and r.ok:
                    st.session_state.video_answer = r.json().get("answer", "")
                    st.session_state.video_sources = r.json().get("sources", [])
                else:
                    st.error(error_text(r))
        if st.session_state.get("video_answer"):
            st.markdown('<div class="panel"><div class="panel-title">AI answer</div>', unsafe_allow_html=True)
            st.markdown(st.session_state.video_answer)
            sources = st.session_state.get("video_sources", [])
            if sources:
                with st.expander("Transcript evidence"):
                    for i, s in enumerate(sources, 1):
                        st.markdown(f"**[{i}]** {s}")
            st.markdown('</div>', unsafe_allow_html=True)

        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("✨ Generate Lecture Summary", use_container_width=True):
                with st.spinner("Creating study notes from the transcript..."):
                    r = api_post(
                        "/youtube/summary",
                        json={"user_id": USER_ID, "video_id": video["video_id"]},
                        timeout=180,
                    )
                if r is not None and r.ok:
                    st.session_state.video_summary = r.json().get("summary", "")
                else:
                    st.error(error_text(r))
        with ac2:
            if st.button("📝 Generate Video Quiz", use_container_width=True):
                with st.spinner("Creating transcript-grounded questions..."):
                    r = api_post(
                        "/youtube/quiz",
                        json={"user_id": USER_ID, "video_id": video["video_id"], "count": 10},
                        timeout=180,
                    )
                if r is not None and r.ok:
                    st.session_state.video_quiz = r.json().get("questions", [])
                else:
                    st.error(error_text(r))

        if st.session_state.get("video_summary"):
            st.markdown('<div class="panel"><div class="panel-title">Lecture study notes</div>', unsafe_allow_html=True)
            st.markdown(st.session_state.video_summary)
            st.markdown('</div>', unsafe_allow_html=True)

        vquiz = st.session_state.get("video_quiz")
        if vquiz:
            st.markdown('<div class="panel"><div class="panel-title">Video quiz</div><div class="panel-sub">Questions are generated only from the indexed transcript.</div>', unsafe_allow_html=True)
            with st.form("video_quiz_form"):
                vals = []
                for i, q in enumerate(vquiz):
                    st.markdown(f"**Q{i+1}. {q['question']}**")
                    vals.append(st.radio("Answer", q["options"], index=None, key=f"vq_{i}", label_visibility="collapsed"))
                    if i < len(vquiz) - 1:
                        st.divider()
                submit_vq = st.form_submit_button("Check Video Quiz", use_container_width=True)
            if submit_vq:
                if any(v is None for v in vals):
                    st.warning("Answer all questions first.")
                else:
                    correct = sum(
                        1 for q, v in zip(vquiz, vals)
                        if q["options"].index(v) == int(q["answer"])
                    )
                    score = round(correct / len(vquiz) * 100, 1)
                    st.session_state.video_quiz_result = {
                        "correct": correct, "total": len(vquiz), "score": score
                    }
            result = st.session_state.get("video_quiz_result")
            if result:
                st.success(
                    f"Video quiz score: {result['score']:.0f}% · "
                    f"{result['correct']}/{result['total']} correct"
                )
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Adaptive Quiz ----------------
with tabs[3]:
    topics=load_topics()
    names=[t["name"] for t in topics]
    st.markdown('<div class="section-title">Adaptive Quiz</div><div class="section-sub">Test a topic and feed the result back into your learning profile.</div>',unsafe_allow_html=True)
    if not names:
        st.markdown('<div class="panel empty-state"><div class="empty-icon">📝</div><b>No topics available</b><br>Upload and process study material first.</div>',unsafe_allow_html=True)
    else:
        selected=st.selectbox("Choose topic",names)
        if st.button("Generate Adaptive Quiz",type="primary"):
            with st.spinner("Generating questions from your material..."):
                r=api_post("/quiz/generate",json={"user_id":USER_ID,"topic":selected,"count":10},timeout=180)
            if r is not None and r.ok: st.session_state.quiz=r.json().get("questions",[]); st.session_state.quiz_topic=selected; st.session_state.pop("quiz_result",None)
            else: st.error(error_text(r))
        quiz=st.session_state.get("quiz")
        if quiz:
            with st.form("quiz_form"):
                answers=[]
                for i,q in enumerate(quiz):
                    st.markdown(f"**Q{i+1}. {q['question']}**")
                    answers.append(st.radio("Answer",q["options"],index=None,key=f"q_{i}",label_visibility="collapsed"))
                    if i<len(quiz)-1: st.divider()
                submitted=st.form_submit_button("Submit Quiz",use_container_width=True)
            if submitted:
                if any(a is None for a in answers): st.warning("Please answer all questions.")
                else:
                    indexes=[q["options"].index(a) for q,a in zip(quiz,answers)]
                    r=api_post("/quiz/submit",json={"user_id":USER_ID,"topic":st.session_state.quiz_topic,"questions":quiz,"answers":indexes},timeout=60)
                    if r is not None and r.ok: st.session_state.quiz_result=r.json(); st.session_state.pop("quiz",None); st.session_state.pop("topics",None); st.rerun()
                    else: st.error(error_text(r))
        result=st.session_state.get("quiz_result")
        if result:
            score=float(result.get("score",0)); a,b,c=st.columns(3); a.metric("Score",f"{score:.0f}%"); b.metric("Correct",f"{result.get('correct',0)}/{result.get('total',0)}"); c.metric("Status","Strong" if score>=75 else "Revision" if score>=50 else "Weak"); st.progress(score/100)

# ---------------- Study Plan ----------------
with tabs[4]:
    topics=load_topics()
    st.markdown('<div class="section-title">Personalized Study Plan</div><div class="section-sub">Prioritize weak areas while keeping stronger topics in revision.</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3); hours=c1.number_input("Hours / day",1.0,12.0,4.0,.5); days=c2.number_input("Days",1,30,3,1); c3.metric("Total capacity",f"{hours*days:g} h")
    if st.button("Generate Adaptive Plan",type="primary",disabled=not topics):
        with st.spinner("Building your plan..."):
            r=api_post("/progress/plan",json={"user_id":USER_ID,"hours":hours,"days":days},timeout=180)
        if r is not None and r.ok: st.session_state.plan=r.json()
        else: st.error(error_text(r))
    plan=st.session_state.get("plan")
    if plan is None:
        r=api_get(f"/progress/plan/{USER_ID}"); plan=r.json() if r is not None and r.ok else []
    if not plan:
        st.markdown('<div class="panel empty-state"><div class="empty-icon">🎯</div><b>No study plan yet</b><br>Generate your adaptive plan after assessing topics.</div>',unsafe_allow_html=True)
    else:
        total=sum(int(x.get("duration",0)) for x in plan); high=sum(x.get("priority")=="HIGH" for x in plan)
        c1,c2,c3=st.columns(3); c1.metric("Planned time",f"{total} min"); c2.metric("Focus topics",len(plan)); c3.metric("High priority",high)
        for item in plan:
            p=item.get("priority","LOW"); icon={"HIGH":"🔴","MEDIUM":"🟡","LOW":"🟢"}.get(p,"⚪")
            st.markdown(f'<div class="panel"><div style="display:flex;justify-content:space-between;gap:20px;align-items:center"><div><div class="panel-title">{icon} {item.get("topic","Topic")}</div><div class="panel-sub" style="margin-bottom:0">{item.get("reason","")}</div></div><div style="font-size:1.1rem;font-weight:850;white-space:nowrap">{item.get("duration",0)} min</div></div></div>',unsafe_allow_html=True)
