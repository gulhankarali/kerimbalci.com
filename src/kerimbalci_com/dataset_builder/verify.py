"""Verifies the `evidence` quotes of dataset records against the downloaded site text.

Each record's `source_url` is mapped to its text file via the manifest, and the
`evidence` is searched verbatim in that text (after Unicode NFC and whitespace
normalization). Records without a source (source_url = null) are skipped.
"""

import json
import logging
from pathlib import Path

from kerimbalci_com.dataset_builder.merge import normalize

logger = logging.getLogger(__name__)


def verify_evidence(records: list[dict], workdir: Path) -> list[str]:
    """Returns a list of problems for records that cannot be verified (empty = all passed)."""
    manifest = json.loads((workdir / "manifest.json").read_text(encoding="utf-8"))
    stem_of = {url: stem for stem, url in manifest.items()}
    texts: dict[str, str] = {}
    problems: list[str] = []

    for record in records:
        url, evidence = record.get("source_url"), record.get("evidence")
        if not url:
            continue
        rid = record.get("id", "<no id>")
        stem = stem_of.get(url)
        if stem is None:
            problems.append(f"{rid}: source_url not in manifest ({url})")
            continue
        if not evidence:
            problems.append(f"{rid}: evidence is empty")
            continue
        if stem not in texts:
            texts[stem] = normalize((workdir / "text" / f"{stem}.txt").read_text(encoding="utf-8"))
        if normalize(evidence) not in texts[stem]:
            problems.append(f"{rid}: evidence not found in {stem}.txt")

    for problem in problems:
        logger.warning(problem)
    return problems
