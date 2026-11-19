"""Compare two evaluation runs side by side.

Usage (from the TanyaCS folder):
    python eval/compare.py baseline marker
"""
import csv
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
IN_SCOPE = ["formal", "slang_abbrev", "typo", "code_mixed_en", "banjar_mixed"]


def load(label):
    with open(RESULTS / f"full_{label}.csv", newline="", encoding="utf-8") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


def rate(rows, field):
    n = len(rows)
    k = sum(1 for r in rows if r[field] == "True")
    return (100 * k / n) if n else float("nan"), n


def main(a_label, b_label):
    a, b = load(a_label), load(b_label)
    ids = [i for i in a if i in b]
    print(f"\n{a_label}  ->  {b_label}   ({len(ids)} questions in both)\n")
    print(f"{'category':<15}{'n':>4}{'correct':>20}{'wrong handoff':>20}")
    for cat in IN_SCOPE:
        ra = [a[i] for i in ids if a[i]["category"] == cat]
        rb = [b[i] for i in ids if b[i]["category"] == cat]
        ca, n = rate(ra, "correct")
        cb, _ = rate(rb, "correct")
        ha, _ = rate(ra, "handoff")
        hb, _ = rate(rb, "handoff")
        print(f"{cat:<15}{n:>4}{ca:>11.1f}% ->{cb:>5.1f}%{ha:>11.1f}% ->{hb:>5.1f}%")
    ra = [a[i] for i in ids if a[i]["category"] in IN_SCOPE]
    rb = [b[i] for i in ids if b[i]["category"] in IN_SCOPE]
    ca, n = rate(ra, "correct")
    cb, _ = rate(rb, "correct")
    ha, _ = rate(ra, "handoff")
    hb, _ = rate(rb, "handoff")
    print(f"{'ALL in-scope':<15}{n:>4}{ca:>11.1f}% ->{cb:>5.1f}%{ha:>11.1f}% ->{hb:>5.1f}%")
    oa = [a[i] for i in ids if a[i]["category"] == "out_of_scope"]
    ob = [b[i] for i in ids if b[i]["category"] == "out_of_scope"]
    xa, n = rate(oa, "correct")
    xb, _ = rate(ob, "correct")
    print(f"{'out_of_scope':<15}{n:>4}{xa:>11.1f}% ->{xb:>5.1f}%   (handed off correctly)")

    better = [i for i in ids if a[i]["correct"] != "True" and b[i]["correct"] == "True"]
    worse = [i for i in ids if a[i]["correct"] == "True" and b[i]["correct"] != "True"]
    print(f"\nNow right ({len(better)}):")
    for i in better:
        print(f"  {i} [{b[i]['category']}] {b[i]['question']}")
    print(f"\nNow wrong ({len(worse)}):")
    for i in worse:
        print(f"  {i} [{b[i]['category']}] {b[i]['question']}")

    newly = [i for i in ids if b[i]["category"] != "out_of_scope"
             and b[i]["handoff"] == "True" and a[i]["handoff"] != "True"]
    print(f"\nIn-scope questions newly handed to a human ({len(newly)}):")
    for i in newly:
        was = "was right" if a[i]["correct"] == "True" else "was wrong"
        print(f"  {i} [{b[i]['category']}] {b[i]['question']}  ({was} before)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python eval/compare.py <label_before> <label_after>")
    main(sys.argv[1], sys.argv[2])