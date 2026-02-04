import streamlit as st
import os
from groq import Groq

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="NOVA AI",
    page_icon="⚪",
    layout="wide"
)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# ---------------- STATE ----------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---------------- LOGIN ----------------
if not st.session_state.current_user:
    st.title("Login")

    username = st.text_input("Username")
    password = ""

    if username.lower() == "ren":
        password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.lower() == "ren" and password != "ayanami":
            st.error("Incorrect password")
            st.stop()

        st.session_state.current_user = username

        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "portal_mode": False,
                "system_prompt": (
                    f"You are Nova, a personal AI assistant. "
                    f"You are speaking directly to {username}. "
                    "Never refer to the user in the third person. "
                    "Be clear, calm, and intelligent."
                )
            }

        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# ---------------- COLORS ----------------
is_ren = st.session_state.current_user.lower() == "ren"
ring_color = "#9bb7d4" if is_ren else "#ffffff"
text_color = ring_color if is_ren else "#ffffff"

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("Settings")

    if st.button("Toggle Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# ---------------- CSS ----------------
st.markdown(
    f"""
    <style>
    body {{
        background-color: #000000;
        color: #ffffff;
    }}

    .portal-container {{
        position: relative;
        width: 100%;
        min-height: 70vh;
        padding-top: 60px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}

    .pulse-ring {{
        width: 160px;
        height: 160px;
        border-radius: 50%;
        border: 4px solid {ring_color};
        animation: pulse 2.2s ease-in-out infinite;
        box-sizing: border-box;
    }}

    @keyframes pulse {{
        0% {{ transform: scale(1); opacity: 0.6; }}
        50% {{ transform: scale(1.08); opacity: 1; }}
        100% {{ transform: scale(1); opacity: 0.6; }}
    }}

    .eye-text {{
        margin-top: 28px;
        width: 100%;
        max-width: 720px;
        padding: 0 16px;
        text-align: center;
        font-size: 16px;
        line-height: 1.6;
        color: {text_color};
        word-wrap: break-word;
    }}

    .typewriter span {{
        opacity: 0;
        animation: appear 0.03s forwards;
    }}

    @keyframes appear {{
        to {{ opacity: 1; }}
    }}

    .user-msg {{
        text-align: right;
        margin: 10px 0;
        color: #cccccc;
    }}

    .nova-msg {{
        text-align: left;
        margin: 10px 0;
        color: #ffffff;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- TYPEWRITER ----------------
def typewriter_html(text):
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    return "".join(
        f"<span style='animation-delay:{i*0.03}s'>{c}</span>"
        for i, c in enumerate(safe)
    )

# ---------------- UI ----------------
if user["portal_mode"]:
    last_answer = ""
    for m in reversed(user["messages"]):
        if m["role"] == "assistant":
            last_answer = m["content"]
            break

    st.markdown(
        f"""
        <div class="portal-container">
            <div class="pulse-ring"></div>
            <div class="eye-text">
                <div class="typewriter">
                    {typewriter_html(last_answer)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for m in user["messages"]:
        cls = "user-msg" if m["role"] == "user" else "nova-msg"
        st.markdown(
            f"<div class='{cls}'>{m['content']}</div>",
            unsafe_allow_html=True
        )

# ---------------- CHAT ----------------
if prompt := st.chat_input("Type a message for Nova"):
    user["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": user["system_prompt"]}]
        + user["messages"][-10:]
    )

    answer = response.choices[0].message.content
    user["messages"].append({"role": "assistant", "content": answer})
    st.rerun()
