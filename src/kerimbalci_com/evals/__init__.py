"""Chatbot eval altyapisi: suite tanimi, paralel runner, hakem ve raporlama.

Calistirma: uv run python -m kerimbalci_com.evals factuality --tags false_premise --limit 5
"""

from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.suite_runner import CaseResult, SuiteResult, run_suite

__all__ = ["CaseResult", "EvalSuite", "SuiteResult", "run_suite"]
