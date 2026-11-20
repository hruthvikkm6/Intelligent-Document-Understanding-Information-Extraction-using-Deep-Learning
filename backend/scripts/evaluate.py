"""Evaluate field exact-match, precision, recall and F1 from labeled JSONL.

Each line: {"prediction": {"field": value}, "truth": {"field": value}}
Values are compared after whitespace/case normalization; no metric is shipped as a claimed result.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def normalize(value):
    return " ".join(str(value).strip().casefold().split()) if value is not None else None


def evaluate(path: Path):
    counts = defaultdict(lambda: [0, 0, 0, 0])  # TP, FP, FN, exact
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        pred, truth = row["prediction"], row["truth"]
        for key in set(pred) | set(truth):
            p, t = normalize(pred.get(key)), normalize(truth.get(key))
            c = counts[key]
            if p is not None and p == t:
                c[0] += 1
            elif p is not None:
                c[1] += 1
            elif t is not None:
                c[2] += 1
            c[3] += int(p == t)
    report = {}
    for key, (tp, fp, fn, exact) in counts.items():
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        report[key] = {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
            "exact_match": exact / sum(counts[key]) if sum(counts[key]) else 0,
            "support": tp + fn,
        }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("labels", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.labels), indent=2))
