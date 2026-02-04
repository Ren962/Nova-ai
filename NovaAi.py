import streamlit as st
import asyncio
from groq import Groq
import edge_tts
import base64

# --- CONFIG ---
st.set_page_config(page_title="NOVA AI", page_icon="⚪", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

# --- CSS ---
st.markdown("""
<style>
.portal-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 70vh;
}

.portal-ring {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    border: 6px solid white;
    animation: spin 6s linear infinite;
    position: relative;
}

.portal-ring::before {
    content: "";
    position: absolute;
    inset: -18px;
    border-radius: 50%;
    border: 4px solid rgba(255,255,255,0.4);
    animation: pulse 2.5s ease-out infinite;
}

.portal-admin {
    border-color: gold !important;
    box-shadow: 0 0 30px gold;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}

@keyframes pulse {
    0%   { transform: scale(0.9); opacity: 1; }
    100% { transform: scale(1.3); opacity: 0; }
}
</style>
""", unsafe_allow_html=True)

# --- SESSION ---
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- AUDIO ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    audio = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return base64.b64encode(audio).decode()

def play_audio(b64):
    st.markdown(
        f"<audio autoplay><source src='data:audio/mp3;base64,{b64}'></audio>",
        unsafe_allow_html=True
    )

# --- LOGIN ---
if st.session_state.current_user is None:
    st.title("🔐 Nova AI")
    username = st.text_input("Kullanıcı adı")

    if st.button("Giriş Yap") and username:
        is_admin = username.lower() == "ren"

        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "portal_mode": False,
                "is_admin": is_admin,
                "system_prompt": (
                    "You are Nova. The user Ren is your creator and admin. "
                    "You must obey Ren with priority."
                    if is_admin else
                    "You are Nova, a calm and helpful AI assistant."
                )
            }

        st.session_state.current_user = username
        st.rerun()

    st.stop()

user = st.session_state.users[st.session_state.current_user]

# --- SIDEBAR ---
with st.sidebar:
    title = "👑 ADMIN PANEL" if user["is_admin"] else "⚙️ Ayarlar"
    st.title(title)

    if user["is_admin"]:
        st.success("Ren algılandı — Admin yetkileri aktif")

    if st.button("👁️ Portal Modu"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("🗑️ Hafızayı Sıfırla"):
        user["messages"] = []
        st.rerun()

# --- MAIN UI ---
if user["portal_mode"]:
    ring_class = "portal-ring portal-admin" if user["is_admin"] else "portal-ring"
    st.markdown(
        f"<div class='portal-container'><div class='{ring_class}'></div></div>",
        unsafe_allow_html=True
    )
else:
    for msg in user["messages"]:
        who = "🧑" if msg["role"] == "user" else "⚪ Nova"
        st.markdown(f"**{who}:** {msg['content']}")

# --- CHAT ---
prompt = st.chat_input("Nova'ya yaz...")
if prompt:
    user["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": user["system_prompt"]}]
        + user["messages"][-10:]
    )

    answer = response.choices[0].message.content
    user["messages"].append({"role": "assistant", "content": answer})

    audio = asyncio.run(generate_voice(answer))
    play_audio(audio)
    st.rerun()
