"""evals.compare: iki rapor arasindaki bozulma/duzelme/puan degisimi tespiti."""

import json
import logging

import pytest

from kerimbalci_com.evals.compare import (
    compare_reports, format_comparison, latest_reports, main,
)


def case(cid, passed, score, tags=("x",), error=None):
    return {"id": cid, "tags": list(tags), "passed": passed, "error": error,
            "metrics": [] if score is None else [{"score": score}]}


def report(suite, started, cases):
    passed = sum(c["passed"] for c in cases)
    stats = {"total": len(cases), "passed": passed, "errored": 0,
             "pass_rate": passed / len(cases), "avg_score": 0.5}
    return {"summary": {"suite": suite, "started_at": started, "overall": stats,
                        "by_tag": {"x": stats}},
            "cases": cases}


OLD = report("factuality-L3", "2026-11-20T10:00:00+00:00", [
    case("a", True, 0.9), case("b", False, 0.2), case("c", True, 0.9),
    case("d", True, 0.95), case("e", False, 0.1),
])
NEW = report("factuality-L3", "2026-11-23T10:00:00+00:00", [
    case("a", False, 0.3), case("b", True, 0.8), case("c", True, 0.65),
    case("d", True, 0.9), case("f", True, 1.0),
])


@pytest.fixture(autouse=True)
def _kok_logger_ayarini_koru():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def test_compare_reports_siniflandirir():
    cmp = compare_reports(OLD, NEW, min_delta=0.2)
    assert [c.id for c in cmp.regressions] == ["a"]
    assert [c.id for c in cmp.fixes] == ["b"]
    assert [c.id for c in cmp.score_changes] == ["c"]  # d: 0.05 < esik
    assert cmp.score_changes[0].delta == pytest.approx(-0.25)
    assert (cmp.added, cmp.removed) == (["f"], ["e"])
    assert cmp.has_regressions


def test_format_comparison_ve_farkli_suite_uyarisi():
    text = format_comparison(compare_reports(OLD, NEW, 0.2))
    assert "Hakem maliyeti" not in text  # eski raporlarda usage yok
    with_cost = {**NEW, "summary": {**NEW["summary"], "overall": {
        **NEW["summary"]["overall"], "usage": {"cost": 0.5}}}}
    old_cost = {**OLD, "summary": {**OLD["summary"], "overall": {
        **OLD["summary"]["overall"], "usage": {"cost": 0.2}}}}
    assert "Hakem maliyeti: $0.2000 -> $0.5000 (+0.3000)" in format_comparison(
        compare_reports(old_cost, with_cost, 0.2))
    assert "BOZULAN (gecti -> kaldi): 1" in text and "a " in text
    assert "UYARI" not in text
    other = report("factuality-L1", "2026-11-24T00:00:00+00:00", NEW["cases"])
    assert "UYARI: farkli suite" in format_comparison(compare_reports(OLD, other, 0.2))


def _write(directory, name, data):
    (directory / name).write_text(json.dumps(data), encoding="utf-8")


def test_latest_reports_ayni_suiteden_son_ikisi(tmp_path):
    _write(tmp_path, "1.json", OLD)
    _write(tmp_path, "2.json", report("factuality-L1", "2026-11-21T00:00:00+00:00", OLD["cases"]))
    _write(tmp_path, "3.json", NEW)
    (tmp_path / "bozuk.json").write_text("{}")
    assert [p.name for p in latest_reports(tmp_path)] == ["1.json", "3.json"]
    assert [p.name for p in latest_reports(tmp_path, "factuality-L1")] == ["2.json"]
    assert latest_reports(tmp_path / "yok") == []


def test_main_cikis_kodlari(monkeypatch, tmp_path):
    monkeypatch.setenv("EVAL_REPORT_DIR", str(tmp_path))
    assert main([]) == 2                     # rapor yok
    _write(tmp_path, "old.json", OLD)
    _write(tmp_path, "new.json", NEW)
    assert main([]) == 1                     # a bozuldu
    assert main([str(tmp_path / "new.json"), str(tmp_path / "new.json")]) == 0
    assert main([str(tmp_path / "old.json"), str(tmp_path / "old.json"), "--min-delta", "0"]) == 0


def test_reporter_ciktisiyla_uyumlu(tmp_path):
    """Gercek reporter'in yazdigi rapor formati compare tarafindan okunabilir."""
    from kerimbalci_com.evals.eval_suite import EvalSuite
    from kerimbalci_com.evals.reporter import write_json_report
    from kerimbalci_com.evals.suite_runner import run_suite
    from deepeval.metrics import BaseMetric

    class Metric(BaseMetric):
        def __init__(self):
            self.threshold = 0.5

        def measure(self, test_case, *a, **k):
            self.score = 1.0 if test_case.actual_output == "dogru" else 0.0
            self.success = self.score >= 0.5
            return self.score

        async def a_measure(self, test_case, *a, **k):
            return self.measure(test_case)

        def is_successful(self):
            return bool(self.success)

    class Bot:
        def __init__(self, answer):
            self.answer = answer

        def ask(self, message):
            return self.answer

    suite = EvalSuite(name="s", description="d",
                      cases=({"id": "a", "input": "q", "expected_output": "e", "tags": ["x"]},),
                      metrics_for=lambda c: [Metric()])
    paths = []
    for answer in ("dogru", "yanlis"):
        result = run_suite(suite, lambda a=answer: Bot(a))
        directory = tmp_path / answer
        paths.append(write_json_report(suite, result, directory))
    cmp = compare_reports(*(json.loads(p.read_text()) for p in paths), min_delta=0.2)
    assert [c.id for c in cmp.regressions] == ["a"]
