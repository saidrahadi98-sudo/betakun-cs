"""Turns the result of ask() into the text shown in the chat, plus a rough language badge."""
import re

BANJAR = {"ulun", "pian", "sampian", "kada", "handak", "kayapa", "kayaapa", "bubuhan", "nang",
          "pabila", "kaina", "dimapa", "manyambung", "mambayari", "wan", "lawan"}
SLANG = {"gk", "ga", "gak", "nggak", "ngga", "gue", "gua", "lu", "aja", "dong", "banget",
         "udah", "udh", "blm", "min", "kok", "sih", "tolong", "tlg", "bs", "yg", "dgn", "krn"}
ENGLISH = {"the", "my", "is", "can", "how", "why", "what", "payment", "bill",
           "slow", "please", "cancel", "not", "working", "i", "to", "do", "subscription"}


def guess_style(text: str) -> str:
    """A rough guess from word lists, shown only as a badge. It can be wrong."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    scores = {
        "Banjar": len(words & BANJAR),
        "Bahasa gaul": len(words & SLANG),
        "English": len(words & ENGLISH),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Indonesia"
    # English words mixed with Indonesian slang are common; call that code-mixing
    if scores["English"] >= 1 and (scores["Bahasa gaul"] >= 1 or scores["Banjar"] >= 1):
        return "Campuran"
    return best


def format_reply(question: str, result: dict) -> str:
    style = guess_style(question)
    lines = [f"`Perkiraan bahasa: {style}`", "", result["answer"]]
    if result["sources"]:
        lines += ["", "**Sumber:** " + ", ".join(s.replace(".md", "") for s in result["sources"])]
    if result["handoff"]:
        lines += ["", "_Pertanyaan ini diteruskan ke agen manusia._"]
    return "\n".join(lines)