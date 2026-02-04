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
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

if "portal_mode" not in st.session_state:
    st.session_state.portal_mode = False

if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False

# --- 3. BEYAZ TEMA CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }

    /* Göz Modu (Portal) Görseli */
    .portal-container { 
        display: flex; justify-content: center; align-items: center; 
        height: 40vh; margin-top: 50px; 
    }
    .pulse-ring {
        width: 120px; height: 120px; border: 3px solid #000; border-radius: 50%;
        animation: pulse 3s infinite ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(0.9); opacity: 0.1; }
        50% { transform: scale(1.1); opacity: 0.5; }
        100% { transform: scale(0.9); opacity: 0.1; }
    }

    /* Metin Alanları */
    .sub-area { text-align: center; font-size: 1.6rem; color: #000; margin-top: 20px; font-weight: 400; }
    .user-msg { color: #888; font-size: 0.9rem; margin-top: 10px; }
    .nova-msg { color: #000; font-size: 1.1rem; font-weight: 500; margin-bottom: 20px; }

    /* Sidebar Düzenleme */
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)


# --- 4. SES VE YAZIM MOTORU ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+10%")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return base64.b64encode(data).decode()


def play_audio(b64_data):
    html_code = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64_data}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(html_code, height=0)


def typewriter(text, placeholder):
    lines = ""
    for char in text:
        lines += char
        placeholder.markdown(f"<div class='sub-area'>{lines}</div>", unsafe_allow_html=True)
        time.sleep(0.03)


# --- 5. AKTİVASYON VE SIDEBAR (AYARLAR) ---
if not st.session_state.audio_ready:
    st.markdown("<div style='text-align:center; margin-top:150px;'><h1>NOVA</h1>", unsafe_allow_html=True)
    if st.button("SİSTEMİ AKTİF ET", use_container_width=True):
        st.session_state.audio_ready = True
        st.rerun()
    st.stop()

with st.sidebar:
    st.title("⚙️ Ayarlar")
    st.write("Nova Kontrol Paneli")

    # Göz Modu Switcher
    mode_label = "Kapat" if st.session_state.portal_mode else "Aç"
    if st.button(f"👁️ Göz Modunu {mode_label}"):
        st.session_state.portal_mode = not st.session_state.portal_mode
        st.rerun()

    # Hafıza Temizleme
    if st.button("🗑️ Hafızayı Sıfırla"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
        st.success("Hafıza temizlendi.")
        st.rerun()

# --- 6. ANA EKRAN VE CHAT ---
if st.session_state.portal_mode:
    st.markdown("<div class='portal-container'><div class='pulse-ring'></div></div>", unsafe_allow_html=True)
    sub_placeholder = st.empty()
else:
    for m in st.session_state.messages:
        div_class = "user-msg" if m["role"] == "user" else "nova-msg"
        label = "Siz" if m["role"] == "user" else "Nova"
        st.markdown(f"<div class='{div_class}'><b>{label}:</b> {m['content']}</div>", unsafe_allow_html=True)

# --- 7. İŞLEME VE YANIT ---
if prompt := st.chat_input("Nova'ya bir şeyler yaz..."):
    # Mesajı Kaydet
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Groq API Yanıtı
    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[{"role": "system", "content": "You are Nova. Be brief and clean."}] + st.session_state.messages[
                -10:]
        )
        answer = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Hafızayı Dosyaya Yaz
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)

        # Sesi Hazırla
        audio_data = asyncio.run(generate_voice(answer))

        # Yanıtı Göster ve Sesi Çal
        if st.session_state.portal_mode:
            play_audio(audio_data)
            typewriter(answer, sub_placeholder)
        else:
            play_audio(audio_data)
            st.rerun()

    except Exception as e:
        st.error(f"Hata: {e}")
