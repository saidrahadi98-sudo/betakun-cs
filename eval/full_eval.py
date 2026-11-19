"""Full evaluation: retrieval, answer correctness (LLM judge) and refusal accuracy, per category.

Usage (from the TanyaCS folder):
    python eval/full_eval.py baseline            # whole test set, label "baseline"
    python eval/full_eval.py baseline limit=20   # quick trial on 20 random questions

Progress is saved after every question, so if it stops (rate limit, no internet) just run the
same command again and it continues. To start over, delete eval/results/full_<label>.jsonl.
"""
import csv
import json
import random
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.answer import ask, retrieve, TOP_K  # noqa: E402

TEST_SET = BASE / "data" / "test_set.csv"
RESULTS_DIR = BASE / "eval" / "results"
K = TOP_K
PAUSE = 4  # seconds between questions, to stay under the free-tier rate limit
IN_SCOPE = ["formal", "slang_abbrev", "typo", "code_mixed_en", "banjar_mixed"]

JUDGE_SYSTEM = (
    "Kamu penilai jawaban customer service. Bandingkan JAWABAN BOT dengan JAWABAN ACUAN untuk "
    "pertanyaan pelanggan. Jawaban bot BENAR jika semua fakta penting (angka, harga, batas waktu, "
    "nama metode, langkah) sesuai dengan acuan dan tidak ada informasi yang bertentangan. Kata-kata "
    "boleh berbeda. Jika ada angka atau fakta yang salah, atau bot hanya menolak atau mengalihkan "
    "ke agen manusia, jawab SALAH. Balas hanya satu kata: BENAR atau SALAH."
)


def load_test_set(path=TEST_SET):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def judge(question, reference, answer, generate_fn):
    user = f"Pertanyaan: {question}\n\nJAWABAN ACUAN: {reference}\n\nJAWABAN BOT: {answer}"
    verdict = generate_fn(JUDGE_SYSTEM, user).upper()
    return "BENAR" in verdict and "SALAH" not in verdict


def evaluate_row(row, retrieve_fn, generate_fn):
    chunks = retrieve_fn(row["question"])
    sources = [c["source"] for c in chunks]
    expected = row["expected_faq"]
    rank = sources.index(expected) + 1 if expected in sources else None

    result = ask(row["question"], retrieve_fn=lambda q: chunks, generate_fn=generate_fn)

    if row["expected_behavior"] == "answer":
        if result["handoff"]:
            correct = False  # it should have answered but handed off
        else:
            correct = judge(row["question"], row["reference_answer"], result["answer"], generate_fn)
    else:
        correct = result["handoff"]  # out of scope: right if it did not try to answer

    return {
        "id": row["id"], "category": row["category"], "question": row["question"],
        "expected_behavior": row["expected_behavior"], "expected_faq": expected,
        "reference_answer": row["reference_answer"], "rank": rank,
        "best_distance": round(result["best_distance"], 3), "handoff": result["handoff"],
        "answer": result["answer"], "sources": result["sources"], "correct": correct,
    }


def pct(n, d):
    return f"{100 * n / d:5.1f}%" if d else "  n/a"


def report(results, label):
    print(f"\n=== Full evaluation ({label}) ===")
    print(f"{'category':<15}{'n':>4}{'hit@' + str(K):>8}{'handoff':>9}{'correct':>9}{'right if answered':>19}")
    tot = {"n": 0, "hit": 0, "ho": 0, "ok": 0, "ans": 0, "ans_ok": 0}
    for cat in IN_SCOPE:
        rs = [r for r in results if r["category"] == cat]
        hit = sum(1 for r in rs if r["rank"] is not None)
        ho = sum(1 for r in rs if r["handoff"])
        ok = sum(1 for r in rs if r["correct"])
        answered = [r for r in rs if not r["handoff"]]
        ans_ok = sum(1 for r in answered if r["correct"])
        print(f"{cat:<15}{len(rs):>4}{pct(hit, len(rs)):>8}{pct(ho, len(rs)):>9}{pct(ok, len(rs)):>9}"
              f"{pct(ans_ok, len(answered)):>19}")
        for k, v in zip(tot, (len(rs), hit, ho, ok, len(answered), ans_ok)):
            tot[k] += v
    print(f"{'ALL in-scope':<15}{tot['n']:>4}{pct(tot['hit'], tot['n']):>8}{pct(tot['ho'], tot['n']):>9}"
          f"{pct(tot['ok'], tot['n']):>9}{pct(tot['ans_ok'], tot['ans']):>19}")
    print("  handoff = share handed to a human by mistake; correct = right answers out of all questions")

    oos = [r for r in results if r["category"] == "out_of_scope"]
    refused = sum(1 for r in oos if r["correct"])
    print(f"\nOut-of-scope: {refused}/{len(oos)} handed off correctly ({pct(refused, len(oos)).strip()})")
    for r in oos:
        if not r["correct"]:
            print(f"  answered when it should not have: {r['question']}")


def save(results, label, results_dir):
    out = results_dir / f"full_{label}.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        cols = ["id", "category", "question", "expected_faq", "rank", "best_distance", "handoff",
                "correct", "answer", "reference_answer"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    # 20% of the judged answers, for you to check by hand (is the judge fair?)
    judged = [r for r in results if r["expected_behavior"] == "answer" and not r["handoff"]]
    sample = random.Random(7).sample(judged, max(1, len(judged) // 5)) if judged else []
    check = results_dir / f"full_{label}_check.csv"
    with open(check, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "question", "reference_answer", "bot_answer", "judge_said_correct", "my_verdict"])
        for r in sample:
            w.writerow([r["id"], r["question"], r["reference_answer"], r["answer"], r["correct"], ""])
    print(f"\nSaved {out.name} and {check.name} ({len(sample)} answers to check by hand) in {results_dir}")


def main(label="baseline", limit=None, retrieve_fn=None, generate_fn=None, pause=PAUSE,
         test_set=TEST_SET, results_dir=RESULTS_DIR):
    retrieve_fn = retrieve_fn or (lambda q: retrieve(q, K))
    if generate_fn is None:
        from src.llm import generate as generate_fn

    rows = load_test_set(test_set)
    if limit:
        rows = random.Random(1).sample(rows, limit)

    results_dir.mkdir(parents=True, exist_ok=True)
    progress = results_dir / f"full_{label}.jsonl"
    done = {}
    if progress.exists():
        for line in progress.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["id"]] = rec

    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(rows)} questions, {len(done)} already done, {len(todo)} to run")
    for i, row in enumerate(todo, 1):
        try:
            rec = evaluate_row(row, retrieve_fn, generate_fn)
        except Exception as e:
            print(f"  {row['id']} failed ({type(e).__name__}: {str(e)[:100]}); run the command again to retry it")
            continue
        done[rec["id"]] = rec
        with open(progress, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  [{i}/{len(todo)}] {rec['id']} {rec['category']}: {'RIGHT' if rec['correct'] else 'WRONG'}")
        time.sleep(pause)

    results = [done[r["id"]] for r in rows if r["id"] in done]
    if len(results) < len(rows):
        print(f"\nWARNING: only {len(results)} of {len(rows)} finished. Run again to finish the rest.")
    report(results, label)
    save(results, label, results_dir)


if __name__ == "__main__":
    args = sys.argv[1:]
    label = next((a for a in args if "=" not in a), "baseline")
    limit = next((int(a.split("=")[1]) for a in args if a.startswith("limit=")), None)
    main(label, limit)