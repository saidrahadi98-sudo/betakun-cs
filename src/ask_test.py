"""Try the bot on a few questions.

Run from the TanyaCS folder:  python -m src.ask_test
"""
from src.answer import ask

QUESTIONS = [
    "min, bayar tagihan bisa lewat apa aja sih?",
    "kok internet gue lemot banget ya min?",
    "Ulun handak berhenti langganan, kayapa caranya?",
    "Kalau telat bayar tagihan kena denda berapa?",
    "Rekomendasi film bagus dong",
]

for q in QUESTIONS:
    r = ask(q)
    print("\nQ:", q)
    print("A:", r["answer"])
    print("Sources:", ", ".join(r["sources"]) or "-",
          "| handoff:", r["handoff"], "| best distance: %.3f" % r["best_distance"])
