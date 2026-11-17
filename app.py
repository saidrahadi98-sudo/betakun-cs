"""Chat page for Tanya CS.  Run from the TanyaCS folder:  python app.py"""
import gradio as gr

from src.answer import ask
from src.format_reply import format_reply

EXAMPLES = [
    "min, bayar tagihan bisa lewat apa aja sih?",
    "Kalau telat bayar tagihan kena denda berapa?",
    "kok internet gue lemot banget ya min?",
    "Ulun handak berhenti langganan, kayapa caranya?",
    "Rekomendasi film bagus dong",
]


def chat(message, history):
    try:
        result = ask(message.strip())
    except Exception:
        return "Maaf, layanan sedang sibuk. Coba lagi sebentar ya."
    return format_reply(message, result)


demo = gr.ChatInterface(
    fn=chat,
    title="Tanya CS - BorneoNet",
    description="Asisten layanan pelanggan BorneoNet (demo, perusahaan fiktif). "
                "Tanya dalam bahasa Indonesia, bahasa gaul, campuran Inggris, atau Banjar.",
    examples=EXAMPLES,
)

if __name__ == "__main__":
    demo.launch()