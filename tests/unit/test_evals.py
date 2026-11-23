"""evals paketinin cevrimdisi testleri: suite, runner, reporter, factuality suite, CLI.

Gercek chatbot veya hakem modeli cagrilmaz; sahte nesneler kullanilir.
"""

import json
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
from kerimbalci_com.evals.suites import SUITES, factuality_suite


class FakeMetric(BaseMetric):
    """Cevap beklenen cevabi iceriyorsa 1.0, yoksa 0.0 verir."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def measure(self, test_case, *args, **kwargs):
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


# --- reporter --------------------------------------------------------------

def test_summarize_ve_json_rapor(tmp_path):
    suite = make_suite()
    result = run_suite(suite, lambda: FakeChatbot(ANSWERS), concurrency=2)
    summary = summarize(suite, result)

    assert summary["overall"] == {"total": 4, "passed": 1, "errored": 2,
                                  "pass_rate": 0.25, "avg_score": 0.5}
    assert summary["by_tag"]["x"]["passed"] == 1 and summary["by_tag"]["y"]["total"] == 3
    assert "overall" in format_summary(summary)

    path = write_json_report(suite, result, tmp_path / "rapor")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.name.startswith("test-")
    assert data["cases"][0]["actual_output"] == "Cevap: Ankara"
    assert data["cases"][0]["metrics"][0]["name"] == "Fake"
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


def test_factuality_esik_ortamdan_ezilir(monkeypatch):
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.9")
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    assert suite.metrics_for(suite.cases[0])[0].threshold == 0.9


# --- CLI -------------------------------------------------------------------

def test_cli_argumanlari():
    args = cli.parse_args(["factuality", "--tags", "a, b", "--ids", "x", "--limit", "3", "--level", "1"])
    assert (args.tags, args.ids, args.limit, args.level) == (["a", "b"], ["x"], 3, 1)
    assert cli.parse_args(["factuality"]).tags is None


def test_cli_eksik_ayarla_2_doner(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "")
    monkeypatch.setenv("JUDGE_MODEL", "")
    assert cli.main(["factuality"]) == 2
