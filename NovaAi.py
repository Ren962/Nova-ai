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

# ---------------- HELPERS ----------------
def typewriter_html(text: str) -> str:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return "".join(
        f"<span style='animation-delay:{i*0.025}s'>{c}</span>"
        for i, c in enumerate(safe)
    )

# ---------------- LOGIN ----------------
if not st.session_state.current_user:
    st.title("Login")

    username = st.text_input("Username")

    password = None
    if username.lower() == "ren":
        password = st.text_input("Admin password", type="password")

    if st.button("Login"):
        if username.lower() == "ren" and password != "ayanami":
            st.error("Invalid admin password")
            st.stop()

        st.session_state.current_user = username

        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "system_prompt": (
                    f"You are Nova, the personal AI assistant for {username}. "
                    "Respond naturally and clearly."
                ),
                "portal_mode": False,
                "is_admin": username.lower() == "ren",
            }

        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("Settings")

    if user["is_admin"]:
        st.info("Admin: Ren")

    if st.button("Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# ---------------- STYLES ----------------
ring_color = "#9bb7d4" if user["is_admin"] else "#000000"

st.markdown(
    f"""
    <style>
    body {{
        background-color: #000000;
        color: #eaeaea;
    }}

    .portal-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 80px;
    }}

    .pulse-ring {{
        width: 160px;
        height: 160px;
        border-radius: 50%;
        border: 4px solid {ring_color};
        animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
        0% {{ transform: scale(1); opacity: 0.8; }}
        50% {{ transform: scale(1.05); opacity: 1; }}
        100% {{ transform: scale(1); opacity: 0.8; }}
    }}

    .eye-text {{
        margin-top: 30px;
        max-width: 700px;
        text-align: center;
        font-size: 16px;
        line-height: 1.6;
    }}

    .typewriter span {{
        opacity: 0;
        animation: appear 0.01s forwards;
    }}

    @keyframes appear {{
        to {{ opacity: 1; }}
    }}

    .user-msg {{
        text-align: right;
        margin: 10px 0;
        color: #9bb7d4;
    }}

    .nova-msg {{
        text-align: left;
        margin: 10px 0;
        color: #eaeaea;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- UI ----------------
if user["portal_mode"]:
    last_answer = ""
    for m in reversed(user["messages"]):
        if m["role"] == "assistant":
            last_answer = m["content"]
            break

    animated = typewriter_html(last_answer)

    st.markdown(
        f"""
        <div class="portal-container">
            <div class="pulse-ring"></div>
            <div class="eye-text">
                <div class="typewriter">{animated}</div>
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
        messages=[
            {"role": "system", "content": user["system_prompt"]}
        ] + user["messages"][-10:]
    )

    answer = response.choices[0].message.content
    user["messages"].append({"role": "assistant", "content": answer})

    st.rerun()
