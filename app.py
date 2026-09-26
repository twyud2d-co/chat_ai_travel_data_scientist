import streamlit as st
import requests
import google.generativeai as genai

# --- 1. PENGATURAN HALAMAN & UI ---
st.title("✈️ Asisten Travel Cerdas (Powered by Gemini)")
st.write("Tanyakan apa saja seputar rencana liburanmu!")

# API key disimpan di .streamlit/secrets.toml, bukan di antarmuka atau source code.
api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- 2. PENGATURAN GAYA BAHASA ---
gaya_bahasa_options = [
    "Santai (seperti teman traveler)",
    "Formal (seperti agen travel profesional)",
]
gaya_bahasa_default = st.secrets.get("app", {}).get(
    "default_chat_style", gaya_bahasa_options[0]
)
if gaya_bahasa_default not in gaya_bahasa_options:
    gaya_bahasa_default = gaya_bahasa_options[0]

with st.sidebar:
    st.header("Pengaturan")
    gaya_bahasa = st.selectbox(
        "Gaya bahasa chatbot:",
        gaya_bahasa_options,
        index=gaya_bahasa_options.index(gaya_bahasa_default),
    )

# --- 3. MENGAMBIL DATA DARI GITHUB ---
@st.cache_data
def ambil_data_github():
    # GANTI URL DI BAWAH INI dengan URL 'Raw' dari file di GitHub Anda
    url = "https://raw.githubusercontent.com/username/repo/main/info_travel.txt"
    try:
        response = requests.get(url)
        return response.text
    except:
        return "Gagal mengambil data referensi travel."

pengetahuan_travel = ambil_data_github()

# --- 4. MEMORI PERCAKAPAN (CHAT HISTORY) ---
if "riwayat_chat" not in st.session_state:
    st.session_state.riwayat_chat = []

# Menampilkan chat lama di layar
# Catatan: Streamlit menggunakan ikon 'assistant', tapi memori Gemini menyimpannya sebagai 'model'
for pesan in st.session_state.riwayat_chat:
    peran_ui = "assistant" if pesan["role"] == "model" else "user"
    with st.chat_message(peran_ui):
        # Gemini menyimpan teks di dalam list bernama 'parts'
        st.markdown(pesan["parts"][0])

# --- 5. LOGIKA CHATBOT & GEMINI API ---
# Jika pengguna mengetik pertanyaan
if pertanyaan := st.chat_input("Ketik pertanyaan travel kamu di sini..."):

    # 1. Tampilkan pertanyaan di layar
    with st.chat_message("user"):
        st.markdown(pertanyaan)

    # 2. Simpan pertanyaan ke memori dengan format yang dikenali Gemini
    st.session_state.riwayat_chat.append({"role": "user", "parts": [pertanyaan]})

    if api_key:
        try:
            # Konfigurasi kunci API Google
            genai.configure(api_key=api_key)

            # Instruksi Rahasia (System Prompt) dimasukkan saat membuat model
            instruksi_sistem = f"""
            Kamu adalah asisten travel.
            Gunakan gaya bahasa: {gaya_bahasa}.

            Gunakan informasi dari database berikut untuk menjawab pertanyaan:
            {pengetahuan_travel}

            Jika informasi yang ditanyakan tidak ada di database, gunakan pengetahuan umummu,
            tapi beritahu pengguna bahwa informasi tersebut bersifat umum.
            """

            # Inisialisasi model Gemini Flash yang tersedia untuk API key ini.
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=instruksi_sistem
            )

            # Memulai sesi obrolan dengan memasukkan riwayat sebelumnya
            # (Kita memotong pertanyaan terakhir [:-1] karena pertanyaan itu akan dikirim via send_message)
            sesi_chat = model.start_chat(history=st.session_state.riwayat_chat[:-1])

            # Mengirim pertanyaan ke Gemini
            respons = sesi_chat.send_message(pertanyaan)
            jawaban_bot = respons.text

            # Tampilkan jawaban di layar
            with st.chat_message("assistant"):
                st.markdown(jawaban_bot)

            # Simpan jawaban ke memori
            st.session_state.riwayat_chat.append({"role": "model", "parts": [jawaban_bot]})

        except Exception as e:
            st.error(f"Terjadi kesalahan saat menghubungi Gemini: {e}")
    else:
        st.warning(
            "Gemini API Key belum diatur. Tambahkan GEMINI_API_KEY di "
            ".streamlit/secrets.toml lalu mulai ulang aplikasi."
        )
