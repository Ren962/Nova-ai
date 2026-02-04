import streamlit as st
import os
from groq import Groq

# --- CONFIG ---
st.set_page_config(page_title="NOVA AI", page_icon="⚪", layout="wide")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# --- CSS ---
st.markdown(
    """
    <style>
    .portal-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
        gap: 20px;
    }

    .pulse-ring {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        border: 6px solid var(--ring-color);
        animation: pulse 2s infinite ease-in-out;
    }

    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.08); opacity: 0.6; }
        100% { transform: scale(1); opacity: 1; }
    }

    .eye-text {
        max-width: 600px;
        text-align: center;
        font-size: 16px;
        line-height: 1.5;
    }

    .user-msg {
        background-color: #f2f2f2;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    .nova-msg {
        background-color: #e6e6e6;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- STATE ---
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- LOGIN ---
if not st.session_state.current_user:
    username = st.text_input("Username")
    if st.button("Login"):
        st.session_state.current_user = username
        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "portal_mode": False,
                "is_admin": username.lower() == "ren",
                "system_prompt": (
                    "You are Nova. You are speaking directly to the user. "
                    "The user is Ren. Do not refer to Ren in the third person. "
                    "Do not ask who the user wants to talk to. "
                    "Be clear, natural, and conversational."
                )
            }
        st.rerun()
    st.stop()

user = st.session_state.users[st.session_state.current_user]

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")

    if user["is_admin"]:
        st.success("Admin user detected")

    if st.button("Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# --- UI ---
if user["portal_mode"]:
    ring_color = "#9bb7d4" if user["is_admin"] else "#000000"
    last_answer = ""
    for m in reversed(user["messages"]):
        if m["role"] == "assistant":
            last_answer = m["content"]
            break

    st.markdown(
        f"""
        <style>
        :root {{
            --ring-color: {ring_color};
        }}
        </style>

        <div class="portal-container">
            <div class="pulse-ring"></div>
            <div class="eye-text">{last_answer}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for m in user["messages"]:
        cls = "user-msg" if m["role"] == "user" else "nova-msg"
        st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)

# --- CHAT ---
if prompt := st.chat_input("Type a message for Nova..."):
    user["messages"].append({"role": "user", "content": prompt})

    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": user["system_prompt"]}
        ] + user["messages"][-10:]
    )

    answer = res.choices[0].message.content
    user["messages"].append({"role": "assistant", "content": answer})
    st.rerun()
