"""Suite sonuclarini raporlar: konsol ozeti (tag bazli) ve JSON dosyasi.

Hakem maliyeti ve token sayilari deepeval metric'lerinden (evaluation_cost,
input_tokens, output_tokens) toplanir. Fiyatlar deepeval'in model tablosundan
gelir; degistirmek icin .env -> ANTHROPIC_COST_PER_INPUT_TOKEN /
ANTHROPIC_COST_PER_OUTPUT_TOKEN (deepeval ayarlari). Chatbot (HF Space) maliyeti
dahil degildir.

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


def case_usage(result: CaseResult) -> dict:
    """Bir case'in tum metric'lerinin hakem maliyeti (USD) ve token toplamlari.

    Hicbir metric maliyet bildirmediyse cost None olur (bilinmiyor != 0).
    """
    costs = [m.evaluation_cost for m in result.metrics if getattr(m, "evaluation_cost", None) is not None]
    return {
        "cost": sum(costs) if costs else None,
        "input_tokens": sum(getattr(m, "input_tokens", None) or 0 for m in result.metrics),
        "output_tokens": sum(getattr(m, "output_tokens", None) or 0 for m in result.metrics),
    }


def _usage_totals(results: list[CaseResult]) -> dict:
    usages = [case_usage(r) for r in results]
    costs = [u["cost"] for u in usages if u["cost"] is not None]
    return {
        "cost": round(sum(costs), 6) if costs else None,
        "input_tokens": sum(u["input_tokens"] for u in usages),
        "output_tokens": sum(u["output_tokens"] for u in usages),
    }


def _metric_name(metric) -> str:
    """GEval adi 'Factuality L3 Advanced (direct_fact) [GEval]' -> 'Factuality L3 Advanced'."""
    name = getattr(metric, "name", None) or type(metric).__name__
    return name.split(" (")[0]


def _by_metric(results: list[CaseResult]) -> dict:
    groups: dict[str, list] = defaultdict(list)
    for result in results:
        for metric in result.metrics:
            groups[_metric_name(metric)].append(metric)
    out = {}
    for name, metrics in sorted(groups.items()):
        scores = [m.score for m in metrics if m.score is not None]
        passed = sum(bool(m.success) and not m.error for m in metrics)
        out[name] = {
            "total": len(metrics),
            "passed": passed,
            "pass_rate": round(passed / len(metrics), 3),
            "avg_score": round(sum(scores) / len(scores), 3) if scores else None,
        }
    return out


def summarize(
    suite: EvalSuite, suite_result: SuiteResult, min_pass_rate: float | None = None
) -> dict:
    """Toplam ve tag bazli gecme orani / ortalama puan; verilirse kalite kapisi sonucu."""
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
            "usage": _usage_totals(results),
        }

    summary = {
        "suite": suite_result.suite_name,
        "started_at": suite_result.started_at.isoformat(),
        "duration_seconds": round(suite_result.duration_seconds, 1),
        "overall": stats(suite_result.results),
        "by_tag": {tag: stats(rs) for tag, rs in sorted(groups.items())},
        "by_metric": _by_metric(suite_result.results),
    }
    if min_pass_rate is not None:
        summary["quality_gate"] = {
            "min_pass_rate": min_pass_rate,
            "pass_rate": round(suite_result.pass_rate, 3),
            "passed": suite_result.meets_quality_gate(min_pass_rate),
        }
    return summary


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
    by_metric = summary.get("by_metric") or {}
    if len(by_metric) > 1:
        lines.append("Metric bazinda:")
        for name, s in by_metric.items():
            avg = "-" if s["avg_score"] is None else f"{s['avg_score']:.2f}"
            lines.append(f"  {name:<30}{s['passed']:>5}/{s['total']:<5}{s['pass_rate']:>6.0%}  ort.puan {avg}")
    usage = summary["overall"].get("usage") or {}
    if usage.get("cost") is not None or usage.get("input_tokens"):
        cost = "-" if usage.get("cost") is None else f"${usage['cost']:.4f}"
        per_case = ""
        if usage.get("cost") is not None and summary["overall"]["total"]:
            per_case = f", case basina ${usage['cost'] / summary['overall']['total']:.4f}"
        lines.append(
            f"Hakem maliyeti: {cost}{per_case} "
            f"({usage.get('input_tokens', 0):,} girdi / {usage.get('output_tokens', 0):,} cikti token)"
        )
    gate = summary.get("quality_gate")
    if gate:
        verdict = "GECTI" if gate["passed"] else "KALDI"
        lines.append(
            f"Kalite kapisi: {verdict} (oran {gate['pass_rate']:.0%}, "
            f"esik {gate['min_pass_rate']:.0%})"
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
        "usage": case_usage(result),
        "metrics": [
            {
                "name": m.__name__ if hasattr(m, "__name__") else type(m).__name__,
                "score": m.score,
                "threshold": m.threshold,
                "success": m.success,
                "reason": m.reason,
                "error": m.error,
                "cost": getattr(m, "evaluation_cost", None),
                "input_tokens": getattr(m, "input_tokens", None),
                "output_tokens": getattr(m, "output_tokens", None),
            }
            for m in result.metrics
        ],
    }


def write_json_report(
    suite: EvalSuite,
    suite_result: SuiteResult,
    directory: Path,
    min_pass_rate: float | None = None,
) -> Path:
    """Ozet + case ayrintilarini <directory>/<suite>-<zaman>.json dosyasina yazar."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = suite_result.started_at.strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{suite_result.suite_name}-{stamp}.json"
    payload = {
        "summary": summarize(suite, suite_result, min_pass_rate),
        "cases": [_case_record(suite, r) for r in suite_result.results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Rapor yazildi: %s", path)
    return path
