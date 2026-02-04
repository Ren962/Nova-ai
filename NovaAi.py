import streamlit as st
import os
from groq import Groq

# --- CONFIG ---
st.set_page_config("NOVA AI", "⚪", layout="wide")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY yok")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# --- STATE ---
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- LOGIN ---
if not st.session_state.current_user:
    username = st.text_input("Kullanıcı adı")
    if st.button("Giriş"):
        st.session_state.current_user = username
        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "system_prompt": f"You are Nova, personal AI for {username}.",
                "portal_mode": False,
                "is_admin": username.lower() == "ren"
            }
        st.rerun()
    st.stop()

user = st.session_state.users[st.session_state.current_user]

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    if user["is_admin"]:
        st.success("ADMIN: Ren")

    if st.button("👁️ Göz Modu"):
        user["portal_mode"] = not user["portal_mode"]
        st.rerun()

    if st.button("🗑️ Hafıza Sıfırla"):
        user["messages"] = []
        st.rerun()

# --- UI ---
if user["portal_mode"]:
    st.markdown("<div class='portal-container'><div class='pulse-ring'></div></div>", unsafe_allow_html=True)
else:
    for m in user["messages"]:
        cls = "user-msg" if m["role"] == "user" else "nova-msg"
        st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)

# --- CHAT ---
if prompt := st.chat_input("Nova'ya yaz..."):
    user["messages"].append({"role": "user", "content": prompt})

    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": user["system_prompt"]}] + user["messages"][-10:]
    )

    answer = res.choices[0].message.content
    user["messages"].append({"role": "assistant", "content": answer})
    st.rerun()
