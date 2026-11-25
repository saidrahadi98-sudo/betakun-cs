"""Start a new run by copying the old results that a cutoff change cannot affect.

Usage (from the BetakunCS folder):
    python eval/seed_run.py marker cutoff45 0.40

Copies every saved result with best_distance <= 0.40 from full_marker.jsonl into
full_cutoff45.jsonl. Then run  python eval/full_eval.py cutoff45  and it only runs the rest.
Only valid when the change is the distance cutoff (retrieval and prompt stay the same).
"""
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def main(src_label, new_label, old_cutoff):
    src = RESULTS / f"full_{src_label}.jsonl"
    dst = RESULTS / f"full_{new_label}.jsonl"
    if dst.exists():
        sys.exit(f"{dst.name} already exists. Delete it first if you want to start over.")
    kept = skipped = 0
    with open(dst, "w", encoding="utf-8") as out:
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["best_distance"] <= old_cutoff:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                kept += 1
            else:
                skipped += 1
    print(f"Copied {kept} results, {skipped} will be re-run.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python eval/seed_run.py <from_label> <new_label> <old_cutoff>")
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))