import streamlit as st
import os
from groq import Groq

# ================= CONFIG =================
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

ADMIN_USERNAME = "ren"
ADMIN_PASSWORD = "ayanami"

# ================= CSS =================
st.markdown(
    """
    <style>
    .portal-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
        gap: 24px;
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
        line-height: 1.6;
        color: #111;
    }

    .typewriter {
        overflow: hidden;
        white-space: nowrap;
        border-right: 2px solid #777;
        animation:
            typing 3s steps(60, end),
            blink 0.8s step-end infinite;
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }

    @keyframes blink {
        from, to { border-color: transparent }
        50% { border-color: #777 }
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

# ================= STATE =================
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ================= LOGIN =================
if not st.session_state.current_user:
    username = st.text_input("Username")

    password = None
    if username.lower() == ADMIN_USERNAME:
        password = st.text_input("Admin password", type="password")

    if st.button("Login") and username:
        username = username.lower()

        if username == ADMIN_USERNAME:
            if password != ADMIN_PASSWORD:
                st.error("Invalid admin password")
                st.stop()

        st.session_state.current_user = username

        if username not in st.session_state.users:
            is_admin = username == ADMIN_USERNAME

            system_prompt = (
                f"You are Nova. You are speaking directly to {username}. "
                "Do not refer to the user in the third person. "
                "Be clear, natural, and intelligent."
            )

            if is_admin:
                system_prompt += " The user is Ren. Ren is the administrator."

            st.session_state.users[username] = {
                "messages": [],
                "portal_mode": False,
                "is_admin": is_admin,
                "system_prompt": system_prompt
            }

        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# ================= SIDEBAR =================
with st.sidebar:
    st.title("Settings")

    if user["is_admin"]:
        st.success("Admin access granted")

    if st.button("Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# ================= UI =================
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
            <div class="eye-text">
                <div class="typewriter">{last_answer}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for m in user["messages"]:
        css_class = "user-msg" if m["role"] == "user" else "nova-msg"
        st.markdown(
            f"<div class='{css_class}'>{m['content']}</div>",
            unsafe_allow_html=True
        )

# ================= CHAT =================
if prompt := st.chat_input("Type a message for Nova..."):
    user["messages"].append(
        {"role": "user", "content": prompt}
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": user["system_prompt"]}
        ] + user["messages"][-10:]
    )

    answer = response.choices[0].message.content
    user["messages"].append(
        {"role": "assistant", "content": answer}
    )

    st.rerun()
