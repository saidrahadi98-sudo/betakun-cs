"""Rewrites Banjarese words and chat slang into standard Indonesian. Used for searching only."""
import csv
import re
from pathlib import Path

WORDS_FILE = Path(__file__).resolve().parent.parent / "data" / "normalization.csv"
_rules = None


def _load():
    global _rules
    if _rules is None:
        pairs = {}
        with open(WORDS_FILE, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                word = row["word"].strip().lower()
                if word and not word.startswith("#"):
                    pairs[word] = row["replacement"].strip()
        keys = sorted(pairs, key=len, reverse=True)  # longest first, so phrases win
        pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b", re.IGNORECASE)
        _rules = (pairs, pattern)
    return _rules


def normalize(text: str) -> str:
    pairs, pattern = _load()

    def swap(match):
        rep = pairs[match.group(0).lower()]
        return "" if rep == "(hapus)" else rep

    out = pattern.sub(swap, text)
    out = re.sub(r"\s+", " ", out).strip()
    return re.sub(r"\s+([?.!,])", r"\1", out)