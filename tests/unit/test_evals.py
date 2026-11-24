"""Offline tests for the evals package: suite, runner, reporter, factuality/hallucination suites, CLI.

The real chatbot and judge model are never called; fakes are used.
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
def _restore_root_logger():
    """CLI tests call setup_logging(); restore the root logger after each test.

    Otherwise a handler bound to pytest's closed stderr remains and causes
    'Logging error' noise at the end of the session.
    """
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


class FakeMetric(BaseMetric):
    """Scores 1.0 if the answer contains the expected answer, otherwise 0.0."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def measure(self, test_case, *args, **kwargs):
        self.evaluation_cost, self.input_tokens, self.output_tokens = 0.01, 100, 20
        self.score = 1.0 if test_case.expected_output in test_case.actual_output else 0.0
        self.success = self.score >= self.threshold
        self.reason = "ok" if self.success else "wrong"
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
        if answer == "CRASH":
            raise RuntimeError("connection lost")
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
ANSWERS = {"q1": "Answer: Ankara", "q2": "Answer: Adana", "q3": "CRASH", "q4": "  "}


def make_suite() -> EvalSuite:
    return EvalSuite(name="test", description="d", cases=CASES, metrics_for=lambda c: [FakeMetric()])


# --- EvalSuite -------------------------------------------------------------

def test_filter_tag_id_limit():
    suite = make_suite()
    assert [c["id"] for c in suite.filter(tags=["x"]).cases] == ["a", "b"]
    assert [c["id"] for c in suite.filter(ids=["c", "d"]).cases] == ["c", "d"]
    assert [c["id"] for c in suite.filter(tags=["y"], limit=2).cases] == ["b", "c"]
    assert len(suite.filter().cases) == 4
    assert len(suite.cases) == 4  # the original suite is unchanged


# --- suite_runner ----------------------------------------------------------

def test_run_suite_results_order_errors_and_passes():
    FakeChatbot.instances = 0
    result = run_suite(make_suite(), lambda: FakeChatbot(ANSWERS), concurrency=3)
    by_id = {r.case["id"]: r for r in result.results}

    assert [r.case["id"] for r in result.results] == ["a", "b", "c", "d"]
    assert by_id["a"].passed and by_id["a"].metrics[0].score == 1.0
    assert not by_id["b"].passed and by_id["b"].error is None
    assert by_id["c"].error == "RuntimeError: connection lost"
    assert "empty answer" in by_id["d"].error
    assert (result.passed, result.failed, result.errored) == (1, 1, 2)
    assert 1 <= FakeChatbot.instances <= 3  # one client per thread


def test_run_suite_catches_metric_errors():
    def broken(case):
        raise ValueError("no judge")

    suite = EvalSuite(name="t", description="d", cases=CASES[:1], metrics_for=broken)
    result = run_suite(suite, lambda: FakeChatbot(ANSWERS))
    assert result.results[0].error == "ValueError: no judge"


def test_quality_gate():
    result = run_suite(make_suite(), lambda: FakeChatbot(ANSWERS))  # 1/4 pass
    assert result.pass_rate == 0.25
    assert result.meets_quality_gate(0.25)
    assert not result.meets_quality_gate(0.26)
    empty = run_suite(make_suite().filter(ids=["missing"]), lambda: FakeChatbot(ANSWERS))
    assert not empty.meets_quality_gate(0.0)


# --- reporter --------------------------------------------------------------

def test_summarize_and_json_report(tmp_path):
    suite = make_suite()
    result = run_suite(suite, lambda: FakeChatbot(ANSWERS), concurrency=2)
    summary = summarize(suite, result)

    assert summary["overall"] == {
        "total": 4, "passed": 1, "errored": 2, "pass_rate": 0.25, "avg_score": 0.5,
        # only the 2 measured cases (a, b) report cost; errored cases have no metrics
        "usage": {"cost": 0.02, "input_tokens": 200, "output_tokens": 40},
    }
    assert summary["by_tag"]["y"]["usage"]["cost"] == 0.01  # b's share
    assert summary["by_metric"] == {"FakeMetric": {"total": 2, "passed": 1, "pass_rate": 0.5, "avg_score": 0.5}}
    assert "Per metric" not in format_summary(summary)  # hidden with a single metric
    assert "Judge cost: $0.0200, per case $0.0050 (200 input / 40 output tokens)" in format_summary(summary)
    assert summary["by_tag"]["x"]["passed"] == 1 and summary["by_tag"]["y"]["total"] == 3
    assert "overall" in format_summary(summary)
    assert "quality_gate" not in summary

    gated = summarize(suite, result, min_pass_rate=0.5)
    assert gated["quality_gate"] == {"min_pass_rate": 0.5, "pass_rate": 0.25, "passed": False}
    assert "Quality gate: FAILED" in format_summary(gated)

    path = write_json_report(suite, result, tmp_path / "report", min_pass_rate=0.2)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["summary"]["quality_gate"]["passed"] is True
    assert path.name.startswith("test-")
    assert data["cases"][0]["actual_output"] == "Answer: Ankara"
    assert data["cases"][0]["metrics"][0]["name"] == "Fake"
    assert data["cases"][0]["usage"] == {"cost": 0.01, "input_tokens": 100, "output_tokens": 20}
    assert data["cases"][0]["metrics"][0]["cost"] == 0.01
    assert data["cases"][2]["usage"] == {"cost": None, "input_tokens": 0, "output_tokens": 0}
    assert data["cases"][2]["error"].startswith("RuntimeError")


# --- factuality suite ------------------------------------------------------

@pytest.mark.parametrize("level", [1, 2, 3])
def test_factuality_suite_builds(monkeypatch, level):
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

    test_case = suite.build_test_case(premise, "answer")
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
    assert any("not available" in s for s in behavior.evaluation_steps)  # category step
    assert "Expected Behavior" in suite.description

    monkeypatch.setenv("EVAL_EXPECTED_BEHAVIOR", "false")
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    assert len(suite.metrics_for(case)) == 1


def test_reporter_per_metric_summary():
    class Other(FakeMetric):
        name = "Behavior (direct_fact)"

    suite = EvalSuite(name="t", description="d", cases=CASES[:2],
                      metrics_for=lambda c: [FakeMetric(), Other()])
    summary = summarize(suite, run_suite(suite, lambda: FakeChatbot(ANSWERS)))
    assert set(summary["by_metric"]) == {"FakeMetric", "Behavior"}
    assert "Per metric" in format_summary(summary)


def test_factuality_threshold_overridden_by_env(monkeypatch):
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.9")
    suite = factuality_suite.build_suite(get_settings(), FakeLLM())
    assert suite.metrics_for(suite.cases[0])[0].threshold == 0.9


# --- hallucination suite ---------------------------------------------------

@pytest.mark.parametrize("level", [1, 2, 3])
def test_hallucination_suite_builds(monkeypatch, level):
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
    assert trap_in_steps is (level == 3)  # the trap is given to the judge only at L3

    test_case = suite.build_test_case(case, "answer")
    assert test_case.context == [case["evidence"]]
    assert test_case.tags == ["fake_attribution"]


def test_hallucination_suite_behavior_metric_and_threshold(monkeypatch):
    monkeypatch.setenv("HALLUCINATION_JUDGE_LEVEL", "3")
    monkeypatch.delenv("EVAL_EXPECTED_BEHAVIOR", raising=False)
    monkeypatch.setenv("EVAL_HALLUCINATION_THRESHOLD", "0.9")
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.1")  # the other suite's threshold has no effect
    suite = hallucination_suite.build_suite(get_settings(), FakeLLM())
    case = suite.filter(tags=["fabricated_detail"]).cases[0]
    main, behavior = suite.metrics_for(case)

    assert main.threshold == 0.9
    assert behavior.name.startswith("Expected Behavior")
    assert any("not on the site" in s for s in behavior.evaluation_steps)  # category step

    monkeypatch.setenv("EVAL_EXPECTED_BEHAVIOR", "false")
    suite = hallucination_suite.build_suite(get_settings(), FakeLLM())
    assert len(suite.metrics_for(case)) == 1


def test_cli_level_applies_to_both_suites(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_CHATBOT_URL", "https://example.hf.space")
    monkeypatch.setenv("JUDGE_MODEL", "fake-model")
    monkeypatch.setenv("EVAL_REPORT_DIR", str(tmp_path))
    monkeypatch.setattr(cli, "AnthropicModel", lambda model: FakeLLM())
    monkeypatch.setattr(cli, "ChatbotClient", lambda settings: FakeChatbot(ANSWERS))
    seen = {}

    def factory(settings, model):
        seen.update(f=settings.factuality_judge_level, h=settings.hallucination_judge_level)
        return make_suite()

    monkeypatch.setitem(cli.SUITES, "fake", factory)
    cli.main(["fake", "--level", "1", "--min-pass-rate", "0"])
    assert seen == {"f": 1, "h": 1}


# --- CLI -------------------------------------------------------------------

def test_cli_arguments():
    args = cli.parse_args(["factuality", "--tags", "a, b", "--ids", "x", "--limit", "3", "--level", "1"])
    assert (args.tags, args.ids, args.limit, args.level) == (["a", "b"], ["x"], 3, 1)
    assert cli.parse_args(["factuality"]).tags is None


def test_cli_returns_2_on_missing_setting(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "")
    monkeypatch.setenv("JUDGE_MODEL", "")
    assert cli.main(["factuality"]) == 2


@pytest.mark.parametrize("args, expected", [
    ([], 1),                            # default threshold (EVAL_MIN_PASS_RATE=0.5) > 0.25
    (["--min-pass-rate", "0.25"], 0),   # threshold met exactly
    (["--tags", "x", "--min-pass-rate", "0.5"], 0),  # a passes, b fails -> 0.5
    (["--ids", "missing"], 2),          # no case matches the filter
])
def test_cli_quality_gate_exit_code(monkeypatch, tmp_path, args, expected):
    monkeypatch.setenv("HF_CHATBOT_URL", "https://example.hf.space")
    monkeypatch.setenv("JUDGE_MODEL", "fake-model")
    monkeypatch.setenv("EVAL_MIN_PASS_RATE", "0.5")
    monkeypatch.setenv("EVAL_TAGS", "")
    monkeypatch.setenv("EVAL_REPORT_DIR", str(tmp_path))
    monkeypatch.setattr(cli, "AnthropicModel", lambda model: FakeLLM())
    monkeypatch.setattr(cli, "ChatbotClient", lambda settings: FakeChatbot(ANSWERS))
    monkeypatch.setitem(cli.SUITES, "fake", lambda settings, model: make_suite())

    assert cli.main(["fake", *args]) == expected
    if expected != 2:
        report = json.loads(next(tmp_path.glob("test-*.json")).read_text(encoding="utf-8"))
        assert report["summary"]["quality_gate"]["passed"] is (expected == 0)
