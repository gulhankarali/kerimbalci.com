"""Runs the cases of a suite in parallel.

For each case: the input is sent to the chatbot -> an LLMTestCase is built ->
the suite's metrics (judges) are measured. EVAL_CONCURRENCY cases run at once.
No error is raised to the caller; it is stored in CaseResult.error, so one
failing case does not stop the whole run.
"""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Protocol

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from kerimbalci_com.evals.eval_suite import Case, EvalSuite

logger = logging.getLogger(__name__)


class Chatbot(Protocol):
    def ask(self, message: str) -> str: ...


@dataclass
class CaseResult:
    """Result of one case: chatbot answer, measured metrics, error and duration."""

    case: Case
    test_case: LLMTestCase | None = None
    metrics: list[BaseMetric] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return self.error is None and bool(self.metrics) and all(
            m.success and not m.error for m in self.metrics
        )


@dataclass
class SuiteResult:
    """Aggregate result of a suite run."""

    suite_name: str
    results: list[CaseResult]
    started_at: datetime
    duration_seconds: float

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def errored(self) -> int:
        return sum(r.error is not None for r in self.results)

    @property
    def failed(self) -> int:
        return len(self.results) - self.passed - self.errored

    @property
    def pass_rate(self) -> float:
        return self.passed / len(self.results) if self.results else 0.0

    def meets_quality_gate(self, min_pass_rate: float) -> bool:
        """Quality gate: pass rate >= min_pass_rate (errored cases count as failures).

        An empty run never passes the gate.
        """
        return bool(self.results) and self.pass_rate >= min_pass_rate


def _run_case(suite: EvalSuite, case: Case, get_chatbot: Callable[[], Chatbot]) -> CaseResult:
    result = CaseResult(case=case)
    start = perf_counter()
    case_id = suite.case_id(case)
    try:
        answer = get_chatbot().ask(case["input"])
        if not answer or not answer.strip():
            raise ValueError("Chatbot returned an empty answer")
        result.test_case = suite.build_test_case(case, answer)
        result.metrics = suite.metrics_for(case)
        for metric in result.metrics:
            metric.measure(result.test_case, _show_indicator=False)
    except Exception as exc:  # noqa: BLE001 — the error is stored in the case result
        result.error = f"{type(exc).__name__}: {exc}"
        logger.warning("%s: error — %s", case_id, result.error)
    result.duration_seconds = perf_counter() - start
    if result.error is None:
        logger.info("%s: %s (%.1fs)", case_id, "PASS" if result.passed else "FAIL",
                    result.duration_seconds)
    return result


def run_suite(
    suite: EvalSuite,
    chatbot_factory: Callable[[], Chatbot],
    concurrency: int = 1,
) -> SuiteResult:
    """Runs the suite. Each worker thread uses its own chatbot client.

    Results are returned in case order.
    """
    concurrency = max(1, concurrency)
    local = threading.local()

    def get_chatbot() -> Chatbot:
        if not hasattr(local, "chatbot"):
            local.chatbot = chatbot_factory()
        return local.chatbot

    logger.info("Suite '%s': %d cases, concurrency %d", suite.name, len(suite.cases), concurrency)
    started_at = datetime.now(timezone.utc)
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="eval") as pool:
        results = list(pool.map(lambda case: _run_case(suite, case, get_chatbot), suite.cases))
    return SuiteResult(
        suite_name=suite.name,
        results=results,
        started_at=started_at,
        duration_seconds=perf_counter() - start,
    )
