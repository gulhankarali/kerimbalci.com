"""Hakem YAML'li (GEval) suite'lerin ortak parcalari.

Bir case iki metric'le olculur:
  1. Ana metric      — suite'in seviyeli hakemi (judges/<suite>_judge/level<N>)
  2. Expected Behavior — dil, kisalik, ton, cerceveleme (EVAL_EXPECTED_BEHAVIOR=false ile kapanir)
Case ancak tum metric'ler gecerse gecmis sayilir.
"""

from collections.abc import Sequence

from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase

from kerimbalci_com.evals.eval_suite import Case, MetricFactory
from kerimbalci_com.evals.judge_config import JudgeConfig, build_geval


def build_test_case(case: Case, answer: str) -> LLMTestCase:
    """Kaydin `evidence` alintisi LLMTestCase.context olur; tag = kategori."""
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
    """Case basina YENI metric listesi ureten fabrika.

    placeholder_fields: kayittaki bu alanlar hakem adimlarindaki {alan}
    yer tutucularini doldurur (eksikse bos metin).
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
