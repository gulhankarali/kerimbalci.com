"""Iki eval kosusunun JSON raporunu karsilastirir (regresyon tespiti).

    uv run python -m kerimbalci_com.evals.compare                       # son iki rapor (ayni suite)
    uv run python -m kerimbalci_com.evals.compare --suite factuality-L3
    uv run python -m kerimbalci_com.evals.compare eski.json yeni.json

Raporlar: EVAL_REPORT_DIR (vars. reports/). Puan degisimi esigi:
EVAL_COMPARE_MIN_DELTA (vars. 0.2). Cikis kodu: 0 bozulma yok, 1 bozulma var,
2 karsilastirilacak rapor bulunamadi.
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

from kerimbalci_com.config import get_settings, setup_logging

logger = logging.getLogger(__name__)


@dataclass
class CaseChange:
    id: str
    tags: list[str]
    old_score: float | None
    new_score: float | None
    old_passed: bool | None
    new_passed: bool | None
    old_error: str | None = None
    new_error: str | None = None

    @property
    def delta(self) -> float | None:
        if self.old_score is None or self.new_score is None:
            return None
        return self.new_score - self.old_score


@dataclass
class Comparison:
    old_suite: str
    new_suite: str
    old_summary: dict
    new_summary: dict
    regressions: list[CaseChange] = field(default_factory=list)   # gecti -> kaldi
    fixes: list[CaseChange] = field(default_factory=list)         # kaldi -> gecti
    score_changes: list[CaseChange] = field(default_factory=list) # durum ayni, puan |d| >= esik
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        return bool(self.regressions)


def _case_score(case: dict) -> float | None:
    scores = [m["score"] for m in case.get("metrics", []) if m.get("score") is not None]
    return sum(scores) / len(scores) if scores else None


def compare_reports(old: dict, new: dict, min_delta: float) -> Comparison:
    """Iki rapor sozlugunu case id'sine gore eslestirip farklari cikarir."""
    old_cases = {c["id"]: c for c in old["cases"]}
    new_cases = {c["id"]: c for c in new["cases"]}
    result = Comparison(
        old_suite=old["summary"]["suite"],
        new_suite=new["summary"]["suite"],
        old_summary=old["summary"],
        new_summary=new["summary"],
        added=sorted(new_cases.keys() - old_cases.keys()),
        removed=sorted(old_cases.keys() - new_cases.keys()),
    )
    for case_id in sorted(old_cases.keys() & new_cases.keys()):
        o, n = old_cases[case_id], new_cases[case_id]
        change = CaseChange(
            id=case_id,
            tags=n.get("tags", []),
            old_score=_case_score(o),
            new_score=_case_score(n),
            old_passed=o.get("passed"),
            new_passed=n.get("passed"),
            old_error=o.get("error"),
            new_error=n.get("error"),
        )
        if o.get("passed") and not n.get("passed"):
            result.regressions.append(change)
        elif not o.get("passed") and n.get("passed"):
            result.fixes.append(change)
        elif change.delta is not None and abs(change.delta) >= min_delta:
            result.score_changes.append(change)
    return result


def _fmt_score(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _fmt_change(c: CaseChange) -> str:
    text = f"  {c.id:<14} [{', '.join(c.tags)}]  {_fmt_score(c.old_score)} -> {_fmt_score(c.new_score)}"
    if c.new_error:
        text += f"  (hata: {c.new_error})"
    return text


def _rate_line(label: str, old: dict | None, new: dict | None) -> str:
    def rate(s):
        return "-" if s is None else f"{s['pass_rate']:.0%}"

    def avg(s):
        return None if s is None else s.get("avg_score")

    o_avg, n_avg = avg(old), avg(new)
    delta = "" if o_avg is None or n_avg is None else f" ({n_avg - o_avg:+.2f})"
    return (f"  {label:<16}{rate(old):>6} -> {rate(new):<6}"
            f"  ort.puan {_fmt_score(o_avg)} -> {_fmt_score(n_avg)}{delta}")


def format_comparison(cmp: Comparison) -> str:
    lines = [f"Karsilastirma: {cmp.old_suite} ({cmp.old_summary['started_at']}) -> "
             f"{cmp.new_suite} ({cmp.new_summary['started_at']})"]
    if cmp.old_suite != cmp.new_suite:
        lines.append("  UYARI: farkli suite/hakem seviyesi karsilastiriliyor")
    old_cost = (cmp.old_summary["overall"].get("usage") or {}).get("cost")
    new_cost = (cmp.new_summary["overall"].get("usage") or {}).get("cost")
    if old_cost is not None and new_cost is not None:
        lines.append(f"Hakem maliyeti: ${old_cost:.4f} -> ${new_cost:.4f} ({new_cost - old_cost:+.4f})")
    lines.append("Gecme orani:")
    lines.append(_rate_line("overall", cmp.old_summary["overall"], cmp.new_summary["overall"]))
    tags = sorted(set(cmp.old_summary["by_tag"]) | set(cmp.new_summary["by_tag"]))
    for tag in tags:
        lines.append(_rate_line(tag, cmp.old_summary["by_tag"].get(tag),
                                cmp.new_summary["by_tag"].get(tag)))
    for title, items in (("BOZULAN (gecti -> kaldi)", cmp.regressions),
                         ("DUZELEN (kaldi -> gecti)", cmp.fixes),
                         ("PUANI DEGISEN", cmp.score_changes)):
        lines.append(f"{title}: {len(items)}")
        lines.extend(_fmt_change(c) for c in items)
    if cmp.added or cmp.removed:
        lines.append(f"Yeni case: {', '.join(cmp.added) or '-'} | Kaldirilan: {', '.join(cmp.removed) or '-'}")
    return "\n".join(lines)


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_reports(directory: Path, suite: str | None = None, count: int = 2) -> list[Path]:
    """Klasordeki raporlardan (istenirse tek suite) en yeni `count` tanesini eskiden yeniye dondurur.

    suite verilmezse en yeni raporun suite'i kullanilir.
    """
    reports = []
    for path in directory.glob("*.json"):
        try:
            summary = load_report(path)["summary"]
        except (KeyError, ValueError):
            continue
        reports.append((summary["started_at"], summary["suite"], path))
    if not reports:
        return []
    reports.sort()
    suite = suite or reports[-1][1]
    return [path for _, name, path in reports if name == suite][-count:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m kerimbalci_com.evals.compare")
    parser.add_argument("reports", nargs="*", type=Path, help="eski.json yeni.json (bos = son iki rapor)")
    parser.add_argument("--suite", default=None, help="ornek: factuality-L3 (vars. en son kosulan)")
    parser.add_argument("--min-delta", type=float, default=None,
                        help="puan degisimi esigi; varsayilan EVAL_COMPARE_MIN_DELTA")
    args = parser.parse_args(argv)
    settings = get_settings()
    setup_logging(settings)

    if len(args.reports) == 2:
        old_path, new_path = args.reports
    elif not args.reports:
        found = latest_reports(settings.eval_report_dir, args.suite)
        if len(found) < 2:
            logger.error("Karsilastirmak icin en az 2 rapor gerekli (%s)", settings.eval_report_dir)
            return 2
        old_path, new_path = found
    else:
        parser.error("ya iki rapor yolu verin ya da hic vermeyin")

    min_delta = args.min_delta if args.min_delta is not None else settings.eval_compare_min_delta
    cmp = compare_reports(load_report(old_path), load_report(new_path), min_delta)
    logger.info("%s -> %s\n%s", old_path.name, new_path.name, format_comparison(cmp))
    return 1 if cmp.has_regressions else 0


if __name__ == "__main__":
    sys.exit(main())
