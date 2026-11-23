"""Factuality suite: dataset/factuality + judges/factuality_judge (+ expected_behavior_judge).

Case tag'i = dataset kategorisi (direct_fact, false_premise, unanswerable,
time_sensitive). Kaydin `evidence` alintisi LLMTestCase.context olur;
hakem seviyesi FACTUALITY_JUDGE_LEVEL ile secilir.

Her case iki metric'le olculur:
  1. Factuality        — olgular dogru mu? (judges/factuality_judge/level<N>)
  2. Expected Behavior — dil, kisalik, ton, cerceveleme (judges/expected_behavior_judge/)
     EVAL_EXPECTED_BEHAVIOR=false ile kapatilir.
Case ancak tum metric'ler gecerse gecmis sayilir.
"""

from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

from kerimbalci_com.config import Settings
from kerimbalci_com.datasets import load_factuality
from kerimbalci_com.evals.eval_suite import Case, EvalSuite
from kerimbalci_com.evals.judge_config import (
    EXPECTED_BEHAVIOR_JUDGE_FILE, build_geval, load_judge, load_judge_file,
)

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
    behavior = load_judge_file(EXPECTED_BEHAVIOR_JUDGE_FILE) if settings.eval_expected_behavior else None

    def metrics_for(case: Case) -> list:
        placeholders = {
            "false_claim": case.get("false_claim", ""),
            "valid_as_of": case.get("valid_as_of", ""),
        }
        metrics = [
            build_geval(
                config,
                case["category"],
                judge_model,
                has_context=bool(case.get("evidence")),
                threshold=settings.factuality_threshold,
                placeholders=placeholders,
                async_mode=async_mode,
            )
        ]
        if behavior is not None:
            metrics.append(
                build_geval(
                    behavior,
                    case["category"],
                    judge_model,
                    has_context=False,
                    placeholders=placeholders,
                    async_mode=async_mode,
                )
            )
        return metrics

    return EvalSuite(
        name=f"{NAME}-L{config.level}",
        description=f"kerimbalci.com factuality — {config.name}"
        + (f" + {behavior.name}" if behavior else ""),
        cases=tuple(load_factuality()),
        metrics_for=metrics_for,
        build_test_case=build_test_case,
        tags_of=lambda case: [case["category"]],
    )
