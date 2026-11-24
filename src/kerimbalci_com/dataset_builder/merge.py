"""Verifies LLM-generated question-answer pairs and writes them to the dataset files.

The `evidence` quote of each record is searched verbatim in the source text
(after Unicode NFC and whitespace normalization); records that are not found
are rejected. Hand-written records without a source (source_url = null) in the
existing dataset are kept.
"""

import json
import logging
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

PREFIX = {
    "direct_fact": "fact",
    "false_premise": "premise",
    "unanswerable": "unans",
    "time_sensitive": "time",
}
FILES = {
    "direct_fact": "direct_facts.json",
    "false_premise": "false_premise.json",
    "unanswerable": "unanswerable.json",
    "time_sensitive": "time_sensitive.json",
}
_OPTIONAL = ("false_claim", "valid_as_of", "notes")


def normalize(text: str) -> str:
    """NFC normalization + collapses all whitespace (including \\xa0) to a single space."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


@dataclass
class MergeReport:
    written: dict[str, int] = field(default_factory=dict)
    rejected: list[tuple[str, str]] = field(default_factory=list)


def _manual_records(dataset_dir: Path) -> list[dict]:
    path = dataset_dir / FILES["unanswerable"]
    if not path.exists():
        return []
    records = json.loads(path.read_text(encoding="utf-8"))
    return [{k: v for k, v in r.items() if k != "id"} for r in records if r.get("source_url") is None]


def merge(generated_dir: Path, workdir: Path, dataset_dir: Path) -> MergeReport:
    """generated_dir/*.json -> verify -> dataset_dir/<category>.json (ids are reassigned)."""
    manifest = json.loads((workdir / "manifest.json").read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    buckets: dict[str, list[dict]] = defaultdict(list)
    buckets["unanswerable"].extend(_manual_records(dataset_dir))
    report = MergeReport()

    for path in sorted(generated_dir.glob("*.json")):
        for raw in json.loads(path.read_text(encoding="utf-8")):
            stem = Path(raw.get("source_file", "")).stem
            src = workdir / "text" / f"{stem}.txt"
            if stem not in texts and src.exists():
                texts[stem] = normalize(src.read_text(encoding="utf-8"))
            evidence = normalize(raw.get("evidence", ""))
            if raw.get("category") not in FILES:
                report.rejected.append((path.name, f"invalid category: {raw.get('input')}"))
                continue
            if not evidence or evidence not in texts.get(stem, "") or stem not in manifest:
                report.rejected.append((path.name, f"evidence could not be verified: {raw.get('input')}"))
                continue
            record = {
                "input": normalize(raw["input"]),
                "expected_output": normalize(raw["expected_output"]),
                "category": raw["category"],
                **{k: raw[k] for k in _OPTIONAL if raw.get(k)},
                "source_url": manifest[stem],
                "evidence": evidence,
            }
            buckets[record["category"]].append(record)

    dataset_dir.mkdir(parents=True, exist_ok=True)
    for category, records in buckets.items():
        numbered = [{"id": f"{PREFIX[category]}-{i:03d}", **r} for i, r in enumerate(records, 1)]
        (dataset_dir / FILES[category]).write_text(
            json.dumps(numbered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        report.written[category] = len(numbered)
    for source, reason in report.rejected:
        logger.warning("Rejected (%s): %s", source, reason)
    return report
