import streamlit as st
import os
from groq import Groq

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="NOVA AI",
    page_icon="⚪",
    layout="wide"
)

# --------------------------------------------------
# SECRETS / API
# --------------------------------------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not configured.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
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
                    "You are Nova. The user Ren is your creator and administrator. "
                    "You must treat Ren with highest priority."
                    if is_admin else
                    "You are Nova, a calm, concise, and helpful AI assistant."
                )
            }

        st.session_state.current_user = username
        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# --------------------------------------------------
# THEME COLORS
# --------------------------------------------------
if user["is_admin"]:
    ACCENT_COLOR = "#9bbcff"   # pale blue
else:
    ACCENT_COLOR = "#ffffff"  # white

# --------------------------------------------------
# GLOBAL CSS
# --------------------------------------------------
st.markdown(f"""
<style>
html, body, [data-testid="stApp"] {{
    background-color: #000000;
    color: {ACCENT_COLOR};
}}

.portal-container {{
    position: fixed;
    inset: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}}

.portal-ring {{
    width: 200px;
    height: 200px;
    border-radius: 50%;
    border: 6px solid {ACCENT_COLOR};
    animation: pulse 2.2s ease-in-out infinite;
}}

@keyframes pulse {{
    0%   {{ transform: scale(0.9); opacity: 0.6; }}
    50%  {{ transform: scale(1.05); opacity: 1; }}
    100% {{ transform: scale(0.9); opacity: 0.6; }}
}}

.chat-user {{
    background-color: #111111;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
}}

.chat-nova {{
    background-color: #0b0b0b;
    padding: 12px;
    border-left: 3px solid {ACCENT_COLOR};
    margin-bottom: 8px;
}}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.title("Admin Panel" if user["is_admin"] else "Settings")

    if user["is_admin"]:
        st.write("Administrator access detected.")

    if st.button("Toggle Eye Mode"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("Clear Memory"):
        user["messages"] = []
        st.rerun()

# --------------------------------------------------
# EYE MODE (PORTAL)
# --------------------------------------------------
if user["portal_mode"]:
    st.markdown(
        "<div class='portal-container'><div class='portal-ring'></div></div>",
        unsafe_allow_html=True
    )
    st.stop()

# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------
for message in user["messages"]:
    if message["role"] == "user":
        st.markdown(
            f"<div class='chat-user'>{message['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='chat-nova'>{message['content']}</div>",
            unsafe_allow_html=True
        )

# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------
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
