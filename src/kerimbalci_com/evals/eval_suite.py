"""Bir eval suite'inin tanimi: hangi case'ler, hangi metric'lerle olculecek.

EvalSuite veri (case listesi) ile olcum mantigini (metric fabrikasi ve
LLMTestCase donusumu) bir arada tutar. Calistirma suite_runner'in isidir.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

Case = dict
MetricFactory = Callable[[Case], list[BaseMetric]]
TestCaseBuilder = Callable[[Case, str], LLMTestCase]


def default_test_case(case: Case, answer: str) -> LLMTestCase:
    """input / expected_output alanlarindan standart LLMTestCase uretir."""
    return LLMTestCase(
        input=case["input"],
        actual_output=answer,
        expected_output=case.get("expected_output"),
        name=case.get("id"),
        tags=list(case.get("tags", [])),
    )


@dataclass(frozen=True)
class EvalSuite:
    """Calistirilabilir bir eval suite'i.

    metrics_for her cagrida YENI metric nesneleri dondurmelidir; deepeval
    metric'leri olcum sonucunu (score, reason) kendi uzerinde tutar.
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
        """Tag ve/veya id'ye gore suzulmus yeni bir suite dondurur (bos = filtre yok)."""
        tags, ids = set(tags), set(ids)
        selected = [
            case for case in self.cases
            if (not tags or tags & set(self.tags_of(case)))
            and (not ids or self.case_id(case) in ids)
        ]
        if limit is not None:
            selected = selected[:limit]
        return replace(self, cases=tuple(selected))
