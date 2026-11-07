"""Score the scrubber against synthetic ground truth (synthetic inputs only).

A labelled span counts as caught only when every alphanumeric character in it lies
inside a detected span, so partial redactions count as misses.
"""

import json
from collections import Counter
from pathlib import Path

from pydantic import SecretStr

from jvsg_triage.etl.ingest import ingest_reports
from jvsg_triage.privacy.scrubber import Redactor
from jvsg_triage.synthetic.notes import LABELS, REQUIRED_RECALL

# Synthetic files carry no real identifiers, so a public fixed key is acceptable here.
EVALUATION_SECRET = SecretStr("synthetic-evaluation-key-not-for-real-data!")


def evaluate_recall(anti_join_csv: Path, case_notes_xlsx: Path, labels_jsonl: Path) -> dict[
    str, object
]:
    """Return per-label recall on cohort-matched notes plus unlabeled detection counts."""
    labels = {
        record["row"]: record["spans"]
        for record in map(json.loads, labels_jsonl.read_text(encoding="utf-8").splitlines())
    }
    batch = ingest_reports(anti_join_csv, case_notes_xlsx, secret=EVALUATION_SECRET)
    redactor = Redactor(batch.lexicon)
    totals: Counter[str] = Counter()
    caught: Counter[str] = Counter()
    unlabeled_detections = 0
    for note in batch.matched_notes:
        text = note.text.get_secret_value()
        detected = redactor.detect(text, (name.get_secret_value() for name in note.context_names))
        covered = bytearray(len(text))
        for span in detected:
            covered[span.start:span.end] = b"\x01" * (span.end - span.start)
        spans = labels[note.source.row_number]
        for span in spans:
            totals[span["label"]] += 1
            positions = [
                index for index in range(span["start"], span["end"]) if text[index].isalnum()
            ]
            if all(covered[index] for index in positions):
                caught[span["label"]] += 1
        unlabeled_detections += sum(
            1 for found in detected
            if not any(found.start < s["end"] and s["start"] < found.end for s in spans)
        )
    recall = {
        label: {"labelled": totals[label], "caught": caught[label],
                "recall": round(caught[label] / totals[label], 4) if totals[label] else None}
        for label in LABELS
    }
    return {
        "notes_evaluated": len(batch.matched_notes),
        "recall": recall,
        "required_labels": list(REQUIRED_RECALL),
        "required_recall_met": all(
            caught[label] == totals[label] for label in REQUIRED_RECALL
        ),
        "unlabeled_detections": unlabeled_detections,
    }
