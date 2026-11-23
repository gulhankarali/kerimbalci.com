"""Factuality suite: dataset/factuality + judges/factuality_judge.

Case tag'i = dataset kategorisi (direct_fact, false_premise, unanswerable,
time_sensitive). Kaydin `evidence` alintisi LLMTestCase.context olur;
hakem seviyesi FACTUALITY_JUDGE_LEVEL ile secilir.
"""

from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_factuality
from kerimbalci_com.evals.eval_suite import Case, EvalSuite
from kerimbalci_com.evals.judge_config import build_geval, load_judge

NAME = "factuality"


def build_test_case(case: Case, answer: str) -> LLMTestCase:
    evidence = case.get("evidence")
    return LLMTestCase(
        input=case["input"],
        actual_output=answer,
        expected_output=case["expected_output"],
        context=[evidence] if evidence else None,
        name=case["id"],
        tags=[case["category"]],
    )


def build_suite(settings: Settings, judge_model: DeepEvalBaseLLM, async_mode: bool = False) -> EvalSuite:
    """Factuality suite'ini kurar. Runner (thread havuzu) icin async_mode=False."""
    config = load_judge(settings.factuality_judge_level)

    def metrics_for(case: Case) -> list:
        return [
            build_geval(
                config,
                case["category"],
                judge_model,
                has_context=bool(case.get("evidence")),
                threshold=settings.factuality_threshold,
                placeholders={
                    "false_claim": case.get("false_claim", ""),
                    "valid_as_of": case.get("valid_as_of", ""),
                },
                async_mode=async_mode,
            )
        ]

    return EvalSuite(
        name=f"{NAME}-L{config.level}",
        description=f"kerimbalci.com factuality — {config.name}",
        cases=tuple(load_factuality()),
        metrics_for=metrics_for,
        build_test_case=build_test_case,
        tags_of=lambda case: [case["category"]],
    )
