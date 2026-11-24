"""Judge (LLM-as-judge) configuration: loading YAML, validation, building GEval.

Criteria are not hardcoded; they are read from
judges/<suite>_judge/<suite>_judge_level<N>_*.yaml (each suite is a `JudgeSet`).
`build_geval` builds a case-specific deepeval GEval metric from this configuration.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from deepeval.metrics import GEval
from deepeval.metrics.g_eval import Rubric
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import SingleTurnParams

from kerimbalci_com.config import PROJECT_ROOT
from kerimbalci_com.datasets import ALL_CATEGORIES, FACTUALITY, HALLUCINATION, DatasetSchema

logger = logging.getLogger(__name__)

JUDGES_ROOT = PROJECT_ROOT / "judges"
EXPECTED_BEHAVIOR_JUDGE_FILE = JUDGES_ROOT / "expected_behavior_judge" / "expected_behavior_judge.yaml"

EVALUATION_PARAMS = frozenset({"input", "actual_output", "expected_output", "context"})
REQUIRED_KEYS = ("name", "level", "description", "threshold", "evaluation_params",
                 "criteria", "evaluation_steps", "rubric")
SCORE_MIN, SCORE_MAX = 0, 10


class JudgeConfigError(ValueError):
    """A judge YAML file does not match the schema."""


@dataclass(frozen=True)
class JudgeSet:
    """The leveled judges of a suite: judges/<prefix>/<prefix>_level<N>_*.yaml."""

    prefix: str
    categories: frozenset[str]

    @classmethod
    def for_dataset(cls, schema: DatasetSchema) -> "JudgeSet":
        return cls(prefix=f"{schema.name}_judge", categories=schema.categories)

    @property
    def directory(self) -> Path:
        return JUDGES_ROOT / self.prefix


FACTUALITY_JUDGES = JudgeSet.for_dataset(FACTUALITY)
HALLUCINATION_JUDGES = JudgeSet.for_dataset(HALLUCINATION)
FACTUALITY_JUDGE_DIR = FACTUALITY_JUDGES.directory
HALLUCINATION_JUDGE_DIR = HALLUCINATION_JUDGES.directory


@dataclass(frozen=True)
class JudgeConfig:
    """Configuration of a single judge level."""

    name: str
    level: int
    description: str
    threshold: float
    evaluation_params: list[str]
    criteria: str
    evaluation_steps: list[str]
    rubric: list[dict]
    rules: list[str] = field(default_factory=list)
    category_steps: dict[str, list[str]] = field(default_factory=dict)
    source: Path | None = None

    def steps_for(self, category: str, **values: str) -> list[str]:
        """General steps + rules + category-specific steps ({placeholder}s are filled)."""
        steps = [
            *self.evaluation_steps,
            *(f"Rule: {rule}" for rule in self.rules),
            *self.category_steps.get(category, []),
        ]
        filled = []
        for step in steps:
            for key, value in values.items():
                step = step.replace("{" + key + "}", value)
            filled.append(step)
        return filled

    def params_for(self, has_context: bool) -> list[str]:
        """Drops the 'context' parameter when there is no evidence."""
        if has_context:
            return list(self.evaluation_params)
        return [p for p in self.evaluation_params if p != "context"]


def _validate(data: dict, path: Path, categories: frozenset[str]) -> None:
    where = path.name
    if not isinstance(data, dict):
        raise JudgeConfigError(f"{where}: the YAML root must be a mapping")
    for key in REQUIRED_KEYS:
        if data.get(key) in (None, "", []):
            raise JudgeConfigError(f"{where}: '{key}' field is missing")
    if not 0 <= float(data["threshold"]) <= 1:
        raise JudgeConfigError(f"{where}: threshold must be between 0 and 1")
    unknown = set(data["evaluation_params"]) - EVALUATION_PARAMS
    if unknown:
        raise JudgeConfigError(f"{where}: unknown evaluation_params {sorted(unknown)}")
    unknown = set(data.get("category_steps") or {}) - categories
    if unknown:
        raise JudgeConfigError(f"{where}: unknown category {sorted(unknown)}")

    ranges = []
    for item in data["rubric"]:
        try:
            low, high = item["score_range"]
            assert item["expected_outcome"]
        except (KeyError, TypeError, ValueError, AssertionError) as exc:
            raise JudgeConfigError(f"{where}: invalid rubric item: {item}") from exc
        ranges.append((int(low), int(high)))
    ranges.sort()
    expected_start = SCORE_MIN
    for low, high in ranges:
        if low != expected_start or high < low:
            raise JudgeConfigError(
                f"{where}: rubric ranges must cover {SCORE_MIN}-{SCORE_MAX} without gaps or "
                f"overlaps (problem range: [{low}, {high}])"
            )
        expected_start = high + 1
    if expected_start != SCORE_MAX + 1:
        raise JudgeConfigError(f"{where}: rubric does not reach {SCORE_MAX}")


def load_judge(
    level: int,
    directory: Path | None = None,
    judges: JudgeSet = FACTUALITY_JUDGES,
) -> JudgeConfig:
    """Loads the judge configuration of the given level (default: factuality)."""
    directory = directory or judges.directory
    matches = sorted(directory.glob(f"{judges.prefix}_level{level}_*.yaml"))
    if len(matches) != 1:
        raise JudgeConfigError(
            f"expected exactly 1 YAML for level {level} in {directory}, "
            f"found {len(matches)}"
        )
    judge = load_judge_file(matches[0], judges.categories)
    if judge.level != level:
        raise JudgeConfigError(f"{matches[0].name}: level in the file ({judge.level}) does not match the file name")
    return judge


def load_judge_file(path: Path, categories: frozenset[str] = ALL_CATEGORIES) -> JudgeConfig:
    """Reads and validates a single judge YAML file.

    category_steps keys must be in `categories`; the default is the categories
    of all suites (for shared judges such as Expected Behavior).
    """
    if not path.is_file():
        raise JudgeConfigError(f"Judge file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(data, path, categories)
    logger.debug("Judge loaded: %s (%s)", data["name"], path.name)
    return JudgeConfig(
        name=data["name"],
        level=int(data["level"]),
        description=" ".join(str(data["description"]).split()),
        threshold=float(data["threshold"]),
        evaluation_params=list(data["evaluation_params"]),
        criteria=" ".join(str(data["criteria"]).split()),
        evaluation_steps=list(data["evaluation_steps"]),
        rubric=list(data["rubric"]),
        rules=list(data.get("rules") or []),
        category_steps={k: list(v) for k, v in (data.get("category_steps") or {}).items()},
        source=path,
    )


def build_geval(
    config: JudgeConfig,
    category: str,
    model: DeepEvalBaseLLM,
    *,
    has_context: bool,
    threshold: float | None = None,
    placeholders: dict[str, str] | None = None,
    async_mode: bool = True,
) -> GEval:
    """Builds a case-specific GEval metric from the configuration.

    If threshold is None the YAML value is used. Pass async_mode=False when
    running in a thread pool.
    """
    return GEval(
        name=f"{config.name} ({category})",
        criteria=config.criteria,
        evaluation_steps=config.steps_for(category, **(placeholders or {})),
        evaluation_params=[SingleTurnParams[p.upper()] for p in config.params_for(has_context)],
        rubric=[
            Rubric(score_range=tuple(r["score_range"]), expected_outcome=r["expected_outcome"])
            for r in config.rubric
        ],
        threshold=config.threshold if threshold is None else threshold,
        model=model,
        async_mode=async_mode,
    )
