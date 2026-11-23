"""Suite sonuclarini raporlar: konsol ozeti (tag bazli) ve JSON dosyasi.

Ayrintili, gecmise donuk karsilastirma icin Confident AI kullanilir
(`deepeval test run`); bu rapor runner kosularinin yerel kaydidir.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path

from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.suite_runner import CaseResult, SuiteResult

logger = logging.getLogger(__name__)


def _scores(result: CaseResult) -> list[float]:
    return [m.score for m in result.metrics if m.score is not None]


def summarize(suite: EvalSuite, suite_result: SuiteResult) -> dict:
    """Toplam ve tag bazli gecme orani / ortalama puan."""
    groups: dict[str, list[CaseResult]] = defaultdict(list)
    for result in suite_result.results:
        for tag in suite.tags_of(result.case) or ["(etiketsiz)"]:
            groups[tag].append(result)

    def stats(results: list[CaseResult]) -> dict:
        scores = [s for r in results for s in _scores(r)]
        return {
            "total": len(results),
            "passed": sum(r.passed for r in results),
            "errored": sum(r.error is not None for r in results),
            "pass_rate": round(sum(r.passed for r in results) / len(results), 3) if results else 0.0,
            "avg_score": round(sum(scores) / len(scores), 3) if scores else None,
        }

    return {
        "suite": suite_result.suite_name,
        "started_at": suite_result.started_at.isoformat(),
        "duration_seconds": round(suite_result.duration_seconds, 1),
        "overall": stats(suite_result.results),
        "by_tag": {tag: stats(rs) for tag, rs in sorted(groups.items())},
    }


def format_summary(summary: dict) -> str:
    """Ozet sozlugunu okunabilir bir tabloya cevirir."""
    rows = [("overall", summary["overall"]), *summary["by_tag"].items()]
    lines = [
        f"Suite: {summary['suite']}  ({summary['duration_seconds']}s)",
        f"{'tag':<18}{'gecen':>8}{'toplam':>8}{'hata':>6}{'oran':>8}{'ort.puan':>10}",
    ]
    for tag, s in rows:
        avg = "-" if s["avg_score"] is None else f"{s['avg_score']:.2f}"
        lines.append(
            f"{tag:<18}{s['passed']:>8}{s['total']:>8}{s['errored']:>6}"
            f"{s['pass_rate']:>8.0%}{avg:>10}"
        )
    return "\n".join(lines)


def _case_record(suite: EvalSuite, result: CaseResult) -> dict:
    return {
        "id": suite.case_id(result.case),
        "tags": list(suite.tags_of(result.case)),
        "input": result.case.get("input"),
        "expected_output": result.case.get("expected_output"),
        "actual_output": result.test_case.actual_output if result.test_case else None,
        "passed": result.passed,
        "error": result.error,
        "duration_seconds": round(result.duration_seconds, 2),
        "metrics": [
            {
                "name": m.__name__ if hasattr(m, "__name__") else type(m).__name__,
                "score": m.score,
                "threshold": m.threshold,
                "success": m.success,
                "reason": m.reason,
                "error": m.error,
            }
            for m in result.metrics
        ],
    }


def write_json_report(suite: EvalSuite, suite_result: SuiteResult, directory: Path) -> Path:
    """Ozet + case ayrintilarini <directory>/<suite>-<zaman>.json dosyasina yazar."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = suite_result.started_at.strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{suite_result.suite_name}-{stamp}.json"
    payload = {
        "summary": summarize(suite, suite_result),
        "cases": [_case_record(suite, r) for r in suite_result.results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Rapor yazildi: %s", path)
    return path
