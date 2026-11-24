"""Shared parts of suites with YAML judges (GEval).

Each case is measured with two metrics:
  1. Main metric       — the suite's leveled judge (judges/<suite>_judge/level<N>)
  2. Expected Behavior — language, concision, tone, framing (disabled with EVAL_EXPECTED_BEHAVIOR=false)
A case passes only if all metrics pass.
"""

from collections.abc import Sequence

from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

from kerimbalci_com.evals.eval_suite import Case, MetricFactory
from kerimbalci_com.evals.judge_config import JudgeConfig, build_geval


def build_test_case(case: Case, answer: str) -> LLMTestCase:
    """The record's `evidence` quote becomes LLMTestCase.context; tag = category."""
    evidence = case.get("evidence")
    return LLMTestCase(
        input=case["input"],
        actual_output=answer,
        expected_output=case["expected_output"],
        context=[evidence] if evidence else None,
        name=case["id"],
        tags=[case["category"]],
    )


def judged_metrics(
    main: JudgeConfig,
    behavior: JudgeConfig | None,
    judge_model: DeepEvalBaseLLM,
    *,
    threshold: float | None,
    placeholder_fields: Sequence[str],
    async_mode: bool,
) -> MetricFactory:
    """Factory that returns a NEW metric list per case.

    placeholder_fields: these record fields fill the {field} placeholders in
    the judge steps (empty string if missing).
    """

    def metrics_for(case: Case) -> list:
        placeholders = {key: case.get(key) or "" for key in placeholder_fields}
        metrics = [
            build_geval(
                main,
                case["category"],
                judge_model,
                has_context=bool(case.get("evidence")),
                threshold=threshold,
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

    return metrics_for
