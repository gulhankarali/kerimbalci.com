"""Dataset uretim komutlari.

    uv run python -m kerimbalci_com.dataset_builder crawl
    uv run python -m kerimbalci_com.dataset_builder split --groups 4
    uv run python -m kerimbalci_com.dataset_builder merge <uretilen_json_klasoru>
    uv run python -m kerimbalci_com.dataset_builder verify hallucination

Yollar ve site adresi .env'den gelir (SITE_URL, SITE_WORKDIR).
"""

import argparse
import logging
import sys
from pathlib import Path

from kerimbalci_com.config import get_settings, setup_logging
from kerimbalci_com.dataset_builder.crawl import crawl, split_groups
from kerimbalci_com.dataset_builder.merge import merge
from kerimbalci_com.dataset_builder.verify import verify_evidence
from kerimbalci_com.datasets import FACTUALITY_DIR, SCHEMAS, load_factuality, load_records

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m kerimbalci_com.dataset_builder")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("crawl", help="siteyi indir ve metne cevir")
    split = sub.add_parser("split", help="metinleri dengeli gruplara bol")
    split.add_argument("--groups", type=int, default=4)
    merge_cmd = sub.add_parser("merge", help="uretilen JSON'lari dogrulayip dataset'e yaz")
    merge_cmd.add_argument("generated_dir", type=Path)
    verify_cmd = sub.add_parser("verify", help="dataset'teki evidence alintilarini site metninde dogrula")
    verify_cmd.add_argument("dataset", choices=sorted(SCHEMAS))
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings)

    if args.command == "crawl":
        crawl(settings)
    elif args.command == "split":
        for i, group in enumerate(split_groups(settings.site_workdir / "text", args.groups), 1):
            logger.info("Grup %d (%d dosya): %s", i, len(group), " ".join(group))
    elif args.command == "verify":
        records = load_records(SCHEMAS[args.dataset])
        problems = verify_evidence(records, settings.site_workdir)
        logger.info("%d kayit kontrol edildi, %d sorun", len(records), len(problems))
        return 1 if problems else 0
    else:
        report = merge(args.generated_dir, settings.site_workdir, FACTUALITY_DIR)
        logger.info("Yazilan: %s | reddedilen: %d", report.written, len(report.rejected))
        load_factuality()  # sema dogrulamasi; hata varsa DatasetError
    return 0


if __name__ == "__main__":
    sys.exit(main())
