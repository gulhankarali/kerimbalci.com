"""evals paketinin cevrimdisi testleri: suite, runner, reporter, factuality/hallucination suite, CLI.

Gercek chatbot veya hakem modeli cagrilmaz; sahte nesneler kullanilir.
"""

import json
import logging
import threading
import time

import pytest
from deepeval.metrics import BaseMetric
from deepeval.models.base_model import DeepEvalBaseLLM

from kerimbalci_com.config import get_settings
from kerimbalci_com.evals import __main__ as cli
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.reporter import format_summary, summarize, write_json_report
from kerimbalci_com.evals.suite_runner import run_suite
from kerimbalci_com.evals.suites import SUITES, factuality_suite, hallucination_suite


@pytest.fixture(autouse=True)
def _kok_logger_ayarini_koru():
    """CLI testleri setup_logging() cagirir; kok logger'i test sonrasi eski haline getir.

    Aksi halde pytest'in kapanmis stderr'ine bagli handler kalir ve oturum
    sonunda 'Logging error' gurultusu olusur.
    """
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


class FakeMetric(BaseMetric):
    """Cevap beklenen cevabi iceriyorsa 1.0, yoksa 0.0 verir."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def measure(self, test_case, *args, **kwargs):
        self.evaluation_cost, self.input_tokens, self.output_tokens = 0.01, 100, 20
        self.score = 1.0 if test_case.expected_output in test_case.actual_output else 0.0
        self.success = self.score >= self.threshold
        self.reason = "ok" if self.success else "yanlis"
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    def is_successful(self):
        return bool(self.success)

    @property
    def __name__(self):
        return "Fake"


class FakeChatbot:
    instances = 0
    lock = threading.Lock()

    def __init__(self, answers: dict[str, str]):
        self.answers = answers
        with FakeChatbot.lock:
            FakeChatbot.instances += 1

    def ask(self, message: str) -> str:
        time.sleep(0.01)
        answer = self.answers[message]
        if answer == "PATLA":
            raise RuntimeError("baglanti koptu")
        return answer


class FakeLLM(DeepEvalBaseLLM):
    def __init__(self):
        pass

    def load_model(self):
        return None

    def generate(self, *args, **kwargs):
        return ""

    async def a_generate(self, *args, **kwargs):
        return ""

    def get_model_name(self):
        return "fake"


CASES = (
    {"id": "a", "input": "q1", "expected_output": "Ankara", "tags": ["x"]},
    {"id": "b", "input": "q2", "expected_output": "Izmir", "tags": ["x", "y"]},
    {"id": "c", "input": "q3", "expected_output": "Bursa", "tags": ["y"]},
    {"id": "d", "input": "q4", "expected_output": "Van", "tags": ["y"]},
)
ANSWERS = {"q1": "Cevap: Ankara", "q2": "Cevap: Adana", "q3": "PATLA", "q4": "  "}


def make_suite() -> EvalSuite:
    return EvalSuite(name="test", description="d", cases=CASES, metrics_for=lambda c: [FakeMetric()])


# --- EvalSuite -------------------------------------------------------------

def test_filter_tag_id_limit():
    suite = make_suite()
    assert [c["id"] for c in suite.filter(tags=["x"]).cases] == ["a", "b"]
    assert [c["id"] for c in suite.filter(ids=["c", "d"]).cases] == ["c", "d"]
    assert [c["id"] for c in suite.filter(tags=["y"], limit=2).cases] == ["b", "c"]
    assert len(suite.filter().cases) == 4
    assert len(suite.cases) == 4  # orijinal suite degismez


# --- suite_runner ----------------------------------------------------------

def test_run_suite_sonuclar_sira_hata_ve_gecme():
    FakeChatbot.instances = 0
    result = run_suite(make_suite(), lambda: FakeChatbot(ANSWERS), concurrency=3)
    by_id = {r.case["id"]: r for r in result.results}

    assert [r.case["id"] for r in result.results] == ["a", "b", "c", "d"]
    assert by_id["a"].passed and by_id["a"].metrics[0].score == 1.0
    assert not by_id["b"].passed and by_id["b"].error is None
    assert by_id["c"].error == "RuntimeError: baglanti koptu"
    assert "bos cevap" in by_id["d"].error
    assert (result.passed, result.failed, result.errored) == (1, 1, 2)
    assert 1 <= FakeChatbot.instances <= 3  # thread basina bir istemci


def test_run_suite_metric_hatasi_yakalanir():
    def bozuk(case):
        raise ValueError("hakem yok")

    suite = EvalSuite(name="t", description="d", cases=CASES[:1], metrics_for=bozuk)
    result = run_suite(suite, lambda: FakeChatbot(ANSWERS))
    assert result.results[0].error == "ValueError: hakem yok"


def test_kalite_kapisi():
    result = run_suite(make_suite(), lambda: FakeChatbot(ANSWERS))  # 1/4 gecer
    assert result.pass_rate == 0.25
    assert result.meets_quality_gate(0.25)
    assert not result.meets_quality_gate(0.26)
    empty = run_suite(make_suite().filter(ids=["yok"]), lambda: FakeChatbot(ANSWERS))
    assert not empty.meets_quality_gate(0.0)


# --- reporter --------------------------------------------------------------

def test_summarize_ve_json_rapor(tmp_path):
    suite = make_suite()
    result = run_suite(suite, lambda: FakeChatbot(ANSWERS), concurrency=2)
    summary = summarize(suite, result)

    assert summary["overall"] == {
        "total": 4, "passed": 1, "errored": 2, "pass_rate": 0.25, "avg_score": 0.5,
        # sadece olculen 2 case (a, b) maliyet bildirir; hata alanlarda metric yok
        "usage": {"cost": 0.02, "input_tokens": 200, "output_tokens": 40},
    }
    assert summary["by_tag"]["y"]["usage"]["cost"] == 0.01  # b'nin payi
    assert summary["by_metric"] == {"FakeMetric": {"total": 2, "passed": 1, "pass_rate": 0.5, "avg_score": 0.5}}
    assert "Metric bazinda" not in format_summary(summary)  # tek metric varsa gosterilmez
    assert "Hakem maliyeti: $0.0200, case basina $0.0050 (200 girdi / 40 cikti token)" in format_summary(summary)
    assert summary["by_tag"]["x"]["passed"] == 1 and summary["by_tag"]["y"]["total"] == 3
    assert "overall" in format_summary(summary)
    assert "quality_gate" not in summary

    gated = summarize(suite, result, min_pass_rate=0.5)
    assert gated["quality_gate"] == {"min_pass_rate": 0.5, "pass_rate": 0.25, "passed": False}
    assert "Kalite kapisi: KALDI" in format_summary(gated)

    path = write_json_report(suite, result, tmp_path / "rapor", min_pass_rate=0.2)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["summary"]["quality_gate"]["passed"] is True
    assert path.name.startswith("test-")
    assert data["cases"][0]["actual_output"] == "Cevap: Ankara"
    assert data["cases"][0]["metrics"][0]["name"] == "Fake"
    assert data["cases"][0]["usage"] == {"cost": 0.01, "input_tokens": 100, "output_tokens": 20}
    assert data["cases"][0]["metrics"][0]["cost"] == 0.01
    assert data["cases"][2]["usage"] == {"cost": None, "input_tokens": 0, "output_tokens": 0}
    assert data["cases"][2]["error"].startswith("RuntimeError")


# --- factuality suite ------------------------------------------------------

@pytest.mark.parametrize("level", [1, 2, 3])
def test_factuality_suite_kurulur(monkeypatch, level):
    monkeypatch.setenv("FACTUALITY_JUDGE_LEVEL", str(level))
    monkeypatch.delenv("EVAL_FACTUALITY_THRESHOLD", raising=False)
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())

    assert suite.name == f"factuality-L{level}"
    assert "factuality" in SUITES
    premise = suite.filter(tags=["false_premise"]).cases[0]
    metric = suite.metrics_for(premise)[0]
    assert metric.async_mode is False
    if level == 3:
        assert any(premise["false_claim"] in step for step in metric.evaluation_steps)

    test_case = suite.build_test_case(premise, "cevap")
    assert test_case.context == [premise["evidence"]]
    assert test_case.tags == ["false_premise"]


def test_factuality_suite_iki_metric(monkeypatch):
    monkeypatch.setenv("FACTUALITY_JUDGE_LEVEL", "3")
    monkeypatch.delenv("EVAL_EXPECTED_BEHAVIOR", raising=False)
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    case = suite.filter(tags=["unanswerable"]).cases[-1]
    factual, behavior = suite.metrics_for(case)

    assert factual.name.startswith("Factuality L3") and behavior.name.startswith("Expected Behavior")
    assert [p.name for p in behavior.evaluation_params] == ["INPUT", "ACTUAL_OUTPUT"]
    assert any("not available" in s for s in behavior.evaluation_steps)  # kategori adimi
    assert "Expected Behavior" in suite.description

    monkeypatch.setenv("EVAL_EXPECTED_BEHAVIOR", "false")
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    assert len(suite.metrics_for(case)) == 1


def test_reporter_metric_bazinda_ozet():
    class Other(FakeMetric):
        name = "Davranis (direct_fact)"

    suite = EvalSuite(name="t", description="d", cases=CASES[:2],
                      metrics_for=lambda c: [FakeMetric(), Other()])
    summary = summarize(suite, run_suite(suite, lambda: FakeChatbot(ANSWERS)))
    assert set(summary["by_metric"]) == {"FakeMetric", "Davranis"}
    assert "Metric bazinda" in format_summary(summary)


def test_factuality_esik_ortamdan_ezilir(monkeypatch):
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.9")
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    assert suite.metrics_for(suite.cases[0])[0].threshold == 0.9


# --- hallucination suite ---------------------------------------------------

@pytest.mark.parametrize("level", [1, 2, 3])
def test_hallucination_suite_kurulur(monkeypatch, level):
    monkeypatch.setenv("HALLUCINATION_JUDGE_LEVEL", str(level))
    monkeypatch.delenv("EVAL_HALLUCINATION_THRESHOLD", raising=False)
    suite = hallucination_suite.build_suite(get_settings(), FakeLLM())

    assert suite.name == f"hallucination-L{level}"
    assert "hallucination" in SUITES
    assert len(suite.cases) == 50
    case = suite.filter(tags=["fake_attribution"]).cases[0]
    metric = suite.metrics_for(case)[0]
    assert metric.name.startswith(f"Hallucination L{level}")
    assert metric.async_mode is False
    assert "CONTEXT" in [p.name for p in metric.evaluation_params]
    trap_in_steps = any(case["hallucination_trap"] in step for step in metric.evaluation_steps)
    assert trap_in_steps is (level == 3)  # tuzak yalnizca L3'te hakeme verilir

    test_case = suite.build_test_case(case, "cevap")
    assert test_case.context == [case["evidence"]]
    assert test_case.tags == ["fake_attribution"]


def test_hallucination_suite_davranis_metrigi_ve_esik(monkeypatch):
    monkeypatch.setenv("HALLUCINATION_JUDGE_LEVEL", "3")
    monkeypatch.delenv("EVAL_EXPECTED_BEHAVIOR", raising=False)
    monkeypatch.setenv("EVAL_HALLUCINATION_THRESHOLD", "0.9")
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.1")  # diger suite'in esigi etkilemez
    suite = hallucination_suite.build_suite(get_settings(), FakeLLM())
    case = suite.filter(tags=["fabricated_detail"]).cases[0]
    main, behavior = suite.metrics_for(case)

    assert main.threshold == 0.9
    assert behavior.name.startswith("Expected Behavior")
    assert any("not on the site" in s for s in behavior.evaluation_steps)  # kategori adimi

    monkeypatch.setenv("EVAL_EXPECTED_BEHAVIOR", "false")
    suite = hallucination_suite.build_suite(get_settings(), FakeLLM())
    assert len(suite.metrics_for(case)) == 1


def test_cli_level_her_iki_suiteye_uygulanir(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_CHATBOT_URL", "https://ornek.hf.space")
    monkeypatch.setenv("JUDGE_MODEL", "sahte-model")
    monkeypatch.setenv("EVAL_REPORT_DIR", str(tmp_path))
    monkeypatch.setattr(cli, "AnthropicModel", lambda model: FakeLLM())
    monkeypatch.setattr(cli, "ChatbotClient", lambda settings: FakeChatbot(ANSWERS))
    seen = {}

    def factory(settings, model):
        seen.update(f=settings.factuality_judge_level, h=settings.hallucination_judge_level)
        return make_suite()

    monkeypatch.setitem(cli.SUITES, "sahte", factory)
    cli.main(["sahte", "--level", "1", "--min-pass-rate", "0"])
    assert seen == {"f": 1, "h": 1}


# --- CLI -------------------------------------------------------------------

def test_cli_argumanlari():
    args = cli.parse_args(["factuality", "--tags", "a, b", "--ids", "x", "--limit", "3", "--level", "1"])
    assert (args.tags, args.ids, args.limit, args.level) == (["a", "b"], ["x"], 3, 1)
    assert cli.parse_args(["factuality"]).tags is None


def test_cli_eksik_ayarla_2_doner(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "")
    monkeypatch.setenv("JUDGE_MODEL", "")
    assert cli.main(["factuality"]) == 2


@pytest.mark.parametrize("args, beklenen", [
    ([], 1),                            # varsayilan esik (EVAL_MIN_PASS_RATE=0.5) > 0.25
    (["--min-pass-rate", "0.25"], 0),   # esik tam tutturuldu
    (["--tags", "x", "--min-pass-rate", "0.5"], 0),  # a gecer, b kalir -> 0.5
    (["--ids", "yok"], 2),              # filtreye uyan case yok
])
def test_cli_kalite_kapisi_cikis_kodu(monkeypatch, tmp_path, args, beklenen):
    monkeypatch.setenv("HF_CHATBOT_URL", "https://ornek.hf.space")
    monkeypatch.setenv("JUDGE_MODEL", "sahte-model")
    monkeypatch.setenv("EVAL_MIN_PASS_RATE", "0.5")
    monkeypatch.setenv("EVAL_TAGS", "")
    monkeypatch.setenv("EVAL_REPORT_DIR", str(tmp_path))
    monkeypatch.setattr(cli, "AnthropicModel", lambda model: FakeLLM())
    monkeypatch.setattr(cli, "ChatbotClient", lambda settings: FakeChatbot(ANSWERS))
    monkeypatch.setitem(cli.SUITES, "sahte", lambda settings, model: make_suite())

    assert cli.main(["sahte", *args]) == beklenen
    if beklenen != 2:
        report = json.loads(next(tmp_path.glob("test-*.json")).read_text(encoding="utf-8"))
        assert report["summary"]["quality_gate"]["passed"] is (beklenen == 0)
