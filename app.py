import streamlit as st
import google.generativeai as genai
from pathlib import Path

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

# --- 3. MEMUAT DATA REFERENSI DARI REPOSITORY ---
@st.cache_data
def ambil_data_referensi():
    nama_file_data = (
        "info_travel.txt",
        "destinasi_wisata.txt",
        "tips_perjalanan.txt",
    )
    bagian_data = []

    for nama_file in nama_file_data:
        path_file = Path(__file__).parent / nama_file
        isi_file = path_file.read_text(encoding="utf-8").strip()
        bagian_data.append(f"=== {nama_file} ===\n{isi_file}")

    return "\n\n".join(bagian_data)

pengetahuan_travel = ambil_data_referensi()

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

                        # Jawaban faktual harus dibatasi pada referensi yang dimuat dari file TXT.
            instruksi_sistem = f"""
            Kamu adalah asisten travel.
            Gunakan gaya bahasa: {gaya_bahasa}.

                        ATURAN WAJIB:
                        - Jawab hanya menggunakan fakta yang secara jelas tertulis dalam database di bawah ini.
                        - Jangan gunakan pengetahuan umum, tebakan, asumsi, atau informasi dari luar database.
                        - Riwayat percakapan hanya boleh dipakai untuk memahami konteks dan rujukan pengguna,
                            bukan sebagai sumber fakta tambahan.
                        - Jika jawaban tidak tersedia atau tidak cukup didukung oleh database, jangan menebak.
                            Jawab: "Maaf, informasi tersebut tidak tersedia di data referensi travel saya."
                        - Jika hanya sebagian pertanyaan didukung data, jawab bagian yang didukung dan jelaskan
                            bahwa bagian lainnya tidak tersedia di data referensi.

                        DATABASE REFERENSI:
            {pengetahuan_travel}
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
