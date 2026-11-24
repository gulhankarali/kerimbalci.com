"""Run a suite from the command line.

    uv run python -m kerimbalci_com.evals factuality
    uv run python -m kerimbalci_com.evals factuality --tags false_premise,unanswerable --limit 5
    uv run python -m kerimbalci_com.evals factuality --ids fact-001,premise-002 --level 1
    uv run python -m kerimbalci_com.evals hallucination --tags fake_attribution --level 1

Defaults come from .env (EVAL_TAGS, EVAL_CONCURRENCY, FACTUALITY_JUDGE_LEVEL,
HALLUCINATION_JUDGE_LEVEL, EVAL_MIN_PASS_RATE).
Exit code: 0 = quality gate passed, 1 = gate failed (pass rate < threshold), 2 = missing setting.
WARNING: makes paid API requests for the judge model.
"""

import argparse
import dataclasses
import logging
import sys

from deepeval.models import AnthropicModel

from kerimbalci_com.chatbot import ChatbotClient
from kerimbalci_com.config import get_settings, setup_logging
from kerimbalci_com.evals.reporter import format_summary, summarize, write_json_report
from kerimbalci_com.evals.suite_runner import run_suite
from kerimbalci_com.evals.suites import SUITES

logger = logging.getLogger(__name__)


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m kerimbalci_com.evals")
    parser.add_argument("suite", choices=sorted(SUITES))
    parser.add_argument("--tags", type=_csv, default=None, help="comma-separated; default EVAL_TAGS")
    parser.add_argument("--ids", type=_csv, default=[], help="comma-separated case ids")
    parser.add_argument("--limit", type=int, default=None, help="at most N cases")
    parser.add_argument("--level", type=int, choices=[1, 2, 3], default=None,
                        help="judge level; default <SUITE>_JUDGE_LEVEL (.env)")
    parser.add_argument("--concurrency", type=int, default=None,
                        help="default EVAL_CONCURRENCY")
    parser.add_argument("--min-pass-rate", type=float, default=None,
                        help="quality gate threshold 0-1; default EVAL_MIN_PASS_RATE")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    if args.level is not None:
        settings = dataclasses.replace(
            settings, factuality_judge_level=args.level, hallucination_judge_level=args.level
        )
    setup_logging(settings)

    missing = [k for k, v in (("HF_CHATBOT_URL", settings.hf_chatbot_url),
                              ("JUDGE_MODEL", settings.judge_model)) if not v]
    if missing:
        logger.error("Missing setting: %s (add it to the .env file)", ", ".join(missing))
        return 2

    judge_model = AnthropicModel(model=settings.judge_model)
    suite = SUITES[args.suite](settings, judge_model).filter(
        tags=args.tags if args.tags is not None else settings.eval_tags,
        ids=args.ids,
        limit=args.limit,
    )
    if not suite.cases:
        logger.error("No case matches the filter")
        return 2

    result = run_suite(
        suite,
        chatbot_factory=lambda: ChatbotClient(settings),
        concurrency=args.concurrency or settings.eval_concurrency,
    )
    min_pass_rate = args.min_pass_rate if args.min_pass_rate is not None else settings.eval_min_pass_rate
    logger.info("\n%s", format_summary(summarize(suite, result, min_pass_rate)))
    write_json_report(suite, result, settings.eval_report_dir, min_pass_rate)
    return 0 if result.meets_quality_gate(min_pass_rate) else 1


if __name__ == "__main__":
    sys.exit(main())
