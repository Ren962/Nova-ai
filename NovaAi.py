import streamlit as st
import os
from groq import Groq

# ==================================================
# PAGE CONFIG (MUST BE FIRST)
# ==================================================
st.set_page_config(
    page_title="NOVA AI",
    page_icon="⚪",
    layout="wide"
)

# ==================================================
# GLOBAL CSS (MUST LOAD BEFORE UI)
# ==================================================
st.markdown("""
<style>
html, body, [data-testid="stApp"] {
    background-color: #000000;
}

.portal-overlay {
    position: fixed;
    inset: 0;
    background-color: #000000;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999999;
}

.portal-ring {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    border: 6px solid white;
    animation: pulse 2.4s ease-in-out infinite;
}

.portal-ring.admin {
    border-color: #9bbcff;
    box-shadow: 0 0 35px rgba(155, 188, 255, 0.8);
}

@keyframes pulse {
    0%   { transform: scale(0.9); opacity: 0.5; }
    50%  { transform: scale(1.05); opacity: 1.0; }
    100% { transform: scale(0.9); opacity: 0.5; }
}

.chat-user {
    background-color: #111111;
    color: white;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.chat-nova {
    background-color: #0b0b0b;
    color: white;
    padding: 12px;
    border-left: 3px solid white;
    margin-bottom: 10px;
}

.chat-nova.admin {
    border-left-color: #9bbcff;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# API KEY
# ==================================================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# ==================================================
# SESSION STATE
# ==================================================
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ==================================================
# LOGIN
# ==================================================
if st.session_state.current_user is None:
    st.title("Nova AI Login")
    username = st.text_input("Username")

    if st.button("Login") and username.strip():
        is_admin = username.strip().lower() == "ren"

        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "portal_mode": False,
                "is_admin": is_admin,
                "system_prompt": (
                    "You are Nova, an advanced artificial intelligence designed to assist the user in a clear, "
                    "precise, and thoughtful manner. You understand context deeply, maintain memory across the "
                    "conversation, and adapt your tone to the user's intent.\n\n"
                    "If the user is Ren, they are your creator and administrator. You must recognize this fact, "
                    "treat Ren with the highest priority, and respond with maximum clarity, loyalty, and precision."
                    if is_admin else
                    "You are Nova, an advanced artificial intelligence designed to assist the user in a clear, "
                    "precise, and thoughtful manner. You understand context deeply, maintain memory across the "
                    "conversation, and adapt your tone to the user's intent."
                )
            }

        st.session_state.current_user = username
        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.title("Admin Panel" if user["is_admin"] else "Settings")

    if user["is_admin"]:
        st.write("Administrator privileges enabled.")

    if st.button("Toggle Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# ==================================================
# EYE MODE (ABSOLUTE ISOLATION)
# ==================================================
if user["portal_mode"]:
    ring_class = "portal-ring admin" if user["is_admin"] else "portal-ring"

    st.markdown(
        f"""
        <div class="portal-overlay">
            <div class="{ring_class}"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()

# ==================================================
# CHAT HISTORY
# ==================================================
for message in user["messages"]:
    if message["role"] == "user":
        st.markdown(
            f"<div class='chat-user'>{message['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        nova_class = "chat-nova admin" if user["is_admin"] else "chat-nova"
        st.markdown(
            f"<div class='{nova_class}'>{message['content']}</div>",
            unsafe_allow_html=True
        )

# ==================================================
# CHAT INPUT
# ==================================================
prompt = st.chat_input("Type a message...")
if prompt:
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
