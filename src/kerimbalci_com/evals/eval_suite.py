"""Definition of an eval suite: which cases are measured with which metrics.

EvalSuite keeps the data (case list) together with the measurement logic
(metric factory and LLMTestCase conversion). Running it is suite_runner's job.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

Case = dict
MetricFactory = Callable[[Case], list[BaseMetric]]
TestCaseBuilder = Callable[[Case, str], LLMTestCase]


def default_test_case(case: Case, answer: str) -> LLMTestCase:
    """Builds a standard LLMTestCase from the input / expected_output fields."""
    return LLMTestCase(
        input=case["input"],
        actual_output=answer,
        expected_output=case.get("expected_output"),
        name=case.get("id"),
        tags=list(case.get("tags", [])),
    )


@dataclass(frozen=True)
class EvalSuite:
    """A runnable eval suite.

    metrics_for must return NEW metric objects on every call; deepeval metrics
    keep the measurement result (score, reason) on themselves.
    """

    name: str
    description: str
    cases: tuple[Case, ...]
    metrics_for: MetricFactory
    build_test_case: TestCaseBuilder = default_test_case
    tags_of: Callable[[Case], Sequence[str]] = lambda case: case.get("tags", [])

    def case_id(self, case: Case) -> str:
        return str(case.get("id", "?"))

    def filter(
        self,
        tags: Iterable[str] = (),
        ids: Iterable[str] = (),
        limit: int | None = None,
    ) -> "EvalSuite":
        """Returns a new suite filtered by tag and/or id (empty = no filter)."""
        tags, ids = set(tags), set(ids)
        selected = [
            case for case in self.cases
            if (not tags or tags & set(self.tags_of(case)))
            and (not ids or self.case_id(case) in ids)
        ]
        if limit is not None:
            selected = selected[:limit]
        return replace(self, cases=tuple(selected))
