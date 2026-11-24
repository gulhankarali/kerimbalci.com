"""Dataset kayitlarinin `evidence` alintilarini indirilmis site metninde dogrular.

Her kaydin `source_url`'i manifest uzerinden metin dosyasina eslenir ve
`evidence` (Unicode NFC + bosluk sadelestirmesinden sonra) o metinde birebir
aranir. Kaynaksiz kayitlar (source_url = null) atlanir.
"""

import json
import logging
from pathlib import Path

from kerimbalci_com.dataset_builder.merge import normalize

logger = logging.getLogger(__name__)


def verify_evidence(records: list[dict], workdir: Path) -> list[str]:
    """Dogrulanamayan kayitlar icin sorun listesi dondurur (bos liste = hepsi gecti)."""
    manifest = json.loads((workdir / "manifest.json").read_text(encoding="utf-8"))
    stem_of = {url: stem for stem, url in manifest.items()}
    texts: dict[str, str] = {}
    problems: list[str] = []

    for record in records:
        url, evidence = record.get("source_url"), record.get("evidence")
        if not url:
            continue
        rid = record.get("id", "<id yok>")
        stem = stem_of.get(url)
        if stem is None:
            problems.append(f"{rid}: source_url manifest'te yok ({url})")
            continue
        if not evidence:
            problems.append(f"{rid}: evidence bos")
            continue
        if stem not in texts:
            texts[stem] = normalize((workdir / "text" / f"{stem}.txt").read_text(encoding="utf-8"))
        if normalize(evidence) not in texts[stem]:
            problems.append(f"{rid}: evidence {stem}.txt icinde bulunamadi")

    for problem in problems:
        logger.warning(problem)
    return problems
