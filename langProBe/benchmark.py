import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Type

import dspy
from dspy.evaluate import Evaluate
from dspy.teleprompt import Teleprompter

import langProBe.optimizers as langprobe_optimizers
from langProBe.dspy_program import LangProBeDSPyMetaProgram


class DSPyFeatures(Enum):
    BASELINE = 0
    OPTIMIZER = 1
    ASSERTION = 2


dataset_size = {"full": None, "lite": 500, "tiny": 200, "test": 50}


class Benchmark(ABC):
    def __init__(self, dataset_mode="lite"):
        # dataset for training and validation
        self.dataset = None
        # dataset for the actual benchmarking
        self.test_set = None
        self.train_set = None
        self.dev_set = None
        self.val_set = None

        self.init_dataset()
        assert self.dataset is not None, "Dataset not initialized"
        assert self.test_set is not None, "Test set not initialized"
        self.max_testset_size = dataset_size[dataset_mode]

        self.test_set = self.trim_dataset(self.test_set, self.max_testset_size)

        # TODO: FIXME: "test" option is for debugging purposes only, should be removed for final release
        if dataset_mode == "test":
            self.dataset = self.trim_dataset(self.dataset, 60)
            self.create_splits()
            self.test_set = self.trim_dataset(self.test_set, 50)

        if not self.train_set or not self.dev_set or not self.val_set:
            self.create_splits()

        self.train_set = self.trim_dataset(self.train_set, 150)
        self.dev_set = self.trim_dataset(self.dev_set, 300)
        self.val_set = self.trim_dataset(self.val_set, 300)

        assert self.train_set is not None, "Train set not initialized"
        assert self.dev_set is not None, "Dev set not initialized"
        assert self.val_set is not None, "Val set not initialized"

    @abstractmethod
    def init_dataset(self) -> None:
        """
        Initializes the dataset for the benchmark, and sets it to self.dataset.
        Each element in the dataset should be an instance of dspy.Example.
        """
        return

    def trim_dataset(self, dataset, size: int) -> None:
        if size is None or size >= len(dataset):
            return dataset
        rng = random.Random()
        rng.seed(1)
        return rng.sample(dataset, size)

    def create_splits(self) -> None:
        """
        Creates the splits for the dataset (not including test).
        Upon completion, self.train_set, self.dev_set, and self.val_set should be set.
        """

        total_len = len(self.dataset)
        self.dev_set = self.dataset[: int(0.4 * total_len)]
        self.val_set = self.dataset[int(0.4 * total_len) : int(0.8 * total_len)]
        self.train_set = self.dataset[int(0.8 * total_len) :]

    def get_dataset(self):
        return self.dataset

    def get_train_set(self):
        return self.train_set

    def get_dev_set(self):
        return self.dev_set

    def get_test_set(self):
        return self.test_set


@dataclass
class EvaluationResult:
    benchmark: str
    program: str

    score: float
    cost: float
    input_tokens: int
    output_tokens: int

    optimizer: str = None
    optimized_program: dspy.Module = None
    optimizer_input_tokens: int = None
    optimizer_output_tokens: int = None
    optimizer_cost: float = None

    optimizer_program_scores: list[float] = None


@dataclass
class BenchmarkMeta:
    benchmark: Type[Benchmark]
    program: List[dspy.Module]
    metric: Callable
    dataset_mode: str = "lite"

    optimizers: List[langprobe_optimizers.OptimizerConfig] = field(
        default_factory=lambda: langprobe_optimizers.DEFAULT_OPTIMIZERS
    )

    # BenchmarkMeta.num_threads has higher priority than run time argument of num_threads
    # use this as an upper bound for the number of threads to use
    num_threads: int = None
    name: str = None


def setup_lm(dspy_config=None):
    lm: dspy.LM = dspy_config.get("lm", dspy.settings.lm)
    assert lm is not None, "dspy language model not set"

    lm = lm.copy()
    assert len(lm.history) == 0, "language model history not empty"
    return lm


def calculate_stats(lm: dspy.LM) -> tuple[float, int, int]:
    cost = 0
    input_tokens = 0
    output_tokens = 0
    for i, trace in enumerate(lm.history):
        cost += trace.get("cost", None) or 0
        input_tokens += trace.get("usage", 0).get("prompt_tokens", 0)
        output_tokens += trace.get("usage", 0).get("completion_tokens", 0)

    return cost, input_tokens, output_tokens


class EvaluateBench(ABC):
    def __init__(
        self,
        benchmark: Benchmark,
        program: dspy.Module,
        metric: Callable,
        lm: str,
        optimizers: list[(Teleprompter, dict)] = None,
        benchmark_name: str = None,
        has_assertions: bool = False,
        num_threads: int = 1,
        use_devset: bool = False,
        evaluate_baseline_flag=True,
        api_key: str = None,
        api_base: str = None,
    ):
        self.evaluate_baseline_flag = evaluate_baseline_flag
        self.features: list[DSPyFeatures] = (
            [DSPyFeatures.BASELINE] if self.evaluate_baseline_flag else []
        )
        self.benchmark = benchmark
        self.program = program
        self.program.setup_lm(lm, api_key=api_key, api_base=api_base)
        self.metric = metric
        self.optimizers = optimizers
        self.num_threads = num_threads
        if use_devset:
            devset = benchmark.get_dev_set()
            print(f"Using devset[{len(devset)}] for evaluation")
        else:
            devset = benchmark.get_test_set()
            print(f"Using testset[{len(devset)}] for evaluation")
        self.evaluate_prog = Evaluate(
            devset=devset,
            metric=self.metric,
            num_threads=self.num_threads,
            display_progress=True,
            # FIXME(shangyin): find a more ergonomic way to set max_errors
            max_errors=5000,
            provide_traceback=False,
        )

        self.program_name = getattr(
            self.program, "_name", self.program.__class__.__name__
        )
        self.benchmark_name = benchmark_name or self.benchmark.__class__.__name__

        self.results: list[EvaluationResult] = []
        if self.optimizers is not None:
            self.features.append(DSPyFeatures.OPTIMIZER)

        if has_assertions:
            self.features.append(DSPyFeatures.ASSERTION)

    def get_empty_results(self):
        return EvaluationResult(
            benchmark=self.benchmark_name,
            program=self.program_name,
            score=0,
            cost=0,
            input_tokens=0,
            output_tokens=0,
        )

    def set_optimizer(self, optimizers: list[Teleprompter]) -> None:
        self.optimizers = optimizers

    def evaluate_baseline(self, dspy_config=None) -> list[EvaluationResult]:
        with dspy.context(**dspy_config):
            score = self.evaluate_prog(self.program)
        result = self.get_empty_results()
        result.score = score
        if isinstance(self.program, LangProBeDSPyMetaProgram):
            result.cost, result.input_tokens, result.output_tokens = calculate_stats(
                self.program.lm
            )
        else:
            # TODO(shangyin): support non-dspy usage.
            result.cost, result.input_tokens, result.output_tokens = 0, 0, 0

        return [result]

    def evaluate_optimizers(self, dspy_config=None) -> list[EvaluationResult]:
        lm = self.program.get_lm()
        self.program.set_lm(None)

        return [
            self.evaluate_with_optimizer(optimizer, optimizer_config, lm, dspy_config)
            for optimizer, optimizer_config in self.optimizers
        ]

    def evaluate_with_optimizer(
        self, optimizer: Teleprompter, optimizer_config, lm, dspy_config=None
    ) -> float:
        result = self.get_empty_results()
        optimizer_lm = lm.copy()
        dspy_config["lm"] = optimizer_lm
        save_candidate_score = optimizer_config.get("save_candidate_score", False)
        with dspy.context(**dspy_config):
            if optimizer_config.get("use_valset", False):
                optimized_program = optimizer(
                    self.program,
                    trainset=self.benchmark.train_set,
                    valset=self.benchmark.val_set,
                )
            else:
                optimized_program = optimizer(
                    self.program, trainset=self.benchmark.train_set
                )
        (
            result.optimizer_cost,
            result.optimizer_input_tokens,
            result.optimizer_output_tokens,
        ) = calculate_stats(optimizer_lm)
        # if save_candidate_score:
        #     score_data = optimized_program.score_data
        #     candidate_scores = [candidate["score"] for candidate in score_data]
        #     result.optimizer_program_scores = candidate_scores

        result.optimizer = optimizer_config.get("name", optimizer.__class__.__name__)
        result.optimized_program = optimized_program

        eval_lm = lm.copy()
        dspy_config["lm"] = eval_lm
        with dspy.context(**dspy_config):
            score = self.evaluate_prog(optimized_program)
        result.score = score
        result.cost, result.input_tokens, result.output_tokens = calculate_stats(
            eval_lm
        )
        return result

    def evaluate_assertion(self, dspy_config=None) -> list[EvaluationResult]:
        self.program.activate_assertions()
        # TODO (shangyin): Implement assertion evaluation with cost metric
        return self.evaluate_prog(self.program)

    def evaluate(self, dspy_config=None) -> list[EvaluationResult]:
        """
        Args:
            dspy_config: A dictionary of configurations for dspy.context
        Returns:
            A list of EvaluationResult objects.
        """
        if dspy_config is None:
            dspy_config = {}
        result = []
        if isinstance(self.program, LangProBeDSPyMetaProgram):
            for feature in self.features:
                match feature:
                    case DSPyFeatures.BASELINE:
                        result.extend(self.evaluate_baseline(dspy_config))
                    case DSPyFeatures.OPTIMIZER:
                        result.extend(self.evaluate_optimizers(dspy_config))
                    case DSPyFeatures.ASSERTION:
                        result.extend(self.evaluate_assertion(dspy_config))
        else:
            # For non-dspy pipelines, only baseline eval is supported for now
            result.extend(self.evaluate_baseline(dspy_config))
        self.results = result
        return result
