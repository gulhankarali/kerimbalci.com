"""Kayitli eval suite'leri. Yeni suite: suites/<ad>.py + buraya ekle."""

from collections.abc import Callable

from deepeval.models import DeepEvalBaseLLM

from kerimbalci_com.config import Settings
from kerimbalci_com.evals.eval_suite import EvalSuite
from kerimbalci_com.evals.suites import factuality_suite

SuiteFactory = Callable[[Settings, DeepEvalBaseLLM], EvalSuite]

SUITES: dict[str, SuiteFactory] = {
    factuality_suite.NAME: factuality_suite.build_suite,
}
