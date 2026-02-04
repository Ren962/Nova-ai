import streamlit as st
import asyncio
from groq import Groq
import edge_tts
import base64
import os
import json
import time

# --- 1. SİSTEM YAPILANDIRMASI ---
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)
PRIMARY_MODEL = "llama-3.3-70b-versatile"
MEMORY_FILE = "nova_memory.json"

st.set_page_config(page_title="NOVA AI", page_icon="⚪", layout="wide")

# --- 2. DURUM YÖNETİMİ (SESSION STATE) ---
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- 3. KULLANICI GİRİŞİ ---
if st.session_state.current_user is None:
    username = st.text_input("Kullanıcı adınızı girin")
    if st.button("Giriş Yap"):
        st.session_state.current_user = username
        if username not in st.session_state.users:
            st.session_state.users[username] = {
                "messages": [],
                "audio_ready": False,
                "portal_mode": False
            }
        st.rerun()

# --- 4. SES VE YAZIM MOTORU ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+10%")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return base64.b64encode(data).decode()

# --- 5. AKTİFASYON VE SIDEBAR (AYARLAR) ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    st.write("Nova Kontrol Paneli")

    # Göz Modu Switcher
    mode_label = "Kapat" if st.session_state.users[st.session_state.current_user]["portal_mode"] else "Aç"
    if st.button(f"👁️ Göz Modunu {mode_label}"):
        st.session_state.users[st.session_state.current_user]["portal_mode"] = not st.session_state.users[st.session_state.current_user]["portal_mode"]
        st.rerun()

    # Hafıza Temizleme
    if st.button("🗑️ Hafızayı Sıfırla"):
        st.session_state.users[st.session_state.current_user]["messages"] = []
        st.success("Hafıza temizlendi.")
        st.rerun()

# --- 6. ANA EKRAN VE CHAT ---
if st.session_state.users[st.session_state.current_user]["portal_mode"]:
    st.markdown("<div class='portal-container'><div class='pulse-ring'></div></div>", unsafe_allow_html=True)
    sub_placeholder = st.empty()
else:
    for m in st.session_state.users[st.session_state.current_user]["messages"]:
        div_class = "user-msg" if m["role"] == "user" else "nova-msg"
        label = "Siz" if m["role"] == "user" else "Nova"
        st.markdown(f"<div class='{div_class}'><b>{label}:</b> {m['content']}</div>", unsafe_allow_html=True)

# --- 7. İŞLEME VE YANIT ---
if prompt := st.chat_input("Nova'ya bir şeyler yaz..."):
    # Mesajı Kaydet
    st.session_state.users[st.session_state.current_user]["messages"].append({"role": "user", "content": prompt})

    # Groq API Yanıtı
    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[{"role": "system", "content": "You are Nova. Be brief and clean."}] + st.session_state.users[st.session_state.current_user]["messages"][-10:]
        )
        answer = response.choices[0].message.content
        st.session_state.users[st.session_state.current_user]["messages"].append({"role": "assistant", "content": answer})

        # Sesi Hazırla
        audio_data = asyncio.run(generate_voice(answer))

        # Yanıtı Göster ve Sesi Çal
        if st.session_state.users[st.session_state.current_user]["portal_mode"]:
            play_audio(audio_data)
            typewriter(answer, sub_placeholder)
        else:
            play_audio(audio_data)
            st.rerun()

    except Exception as e:
        st.error(f"Hata: {e}")
