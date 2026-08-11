"""Public interface of the ExperimentOS statistical engine."""

from experiment_os_stats.analyses import (
    fisher_exact_test,
    mann_whitney_u_test,
    permutation_mean_test,
    student_t_test,
    two_proportion_z_test,
    welch_t_test,
)
from experiment_os_stats.data import (
    SampleValidationSummary,
    ValidatedABData,
    ValidatedSample,
    validate_ab_samples,
    validate_binary_sample,
    validate_continuous_sample,
)
from experiment_os_stats.descriptive import (
    BinaryABSummary,
    BinaryComparisonSummary,
    BinaryGroupSummary,
    ContinuousABSummary,
    ContinuousComparisonSummary,
    ContinuousGroupSummary,
    summarize_binary_ab,
    summarize_binary_sample,
    summarize_continuous_ab,
    summarize_continuous_sample,
)
from experiment_os_stats.diagnostics import (
    BinaryRatePlotData,
    BoxplotData,
    ContinuousDistributionPlotData,
    HistogramData,
    QQPlotData,
    binary_rate_plot_data,
    continuous_distribution_plot_data,
)
from experiment_os_stats.exceptions import (
    DataValidationError,
    DegenerateSampleError,
    ExperimentOSError,
    IncompatibleMetricError,
    InsufficientSampleError,
    InvalidParameterError,
)
from experiment_os_stats.results import (
    ConfidenceInterval,
    StatisticalResult,
    StatisticalWarning,
)
from experiment_os_stats.simulation import (
    BinarySimulationResult,
    ContinuousDistribution,
    ContinuousSimulationResult,
    simulate_binary_ab,
    simulate_continuous_ab,
)
from experiment_os_stats.types import (
    Alternative,
    DataSource,
    MetricType,
    MissingValuePolicy,
    WarningSeverity,
)

__all__ = [
    "Alternative",
    "BinaryABSummary",
    "BinaryComparisonSummary",
    "BinaryGroupSummary",
    "BinaryRatePlotData",
    "BinarySimulationResult",
    "BoxplotData",
    "ConfidenceInterval",
    "ContinuousABSummary",
    "ContinuousComparisonSummary",
    "ContinuousDistribution",
    "ContinuousDistributionPlotData",
    "ContinuousGroupSummary",
    "ContinuousSimulationResult",
    "DataSource",
    "DataValidationError",
    "DegenerateSampleError",
    "ExperimentOSError",
    "IncompatibleMetricError",
    "InsufficientSampleError",
    "InvalidParameterError",
    "MetricType",
    "MissingValuePolicy",
    "HistogramData",
    "QQPlotData",
    "SampleValidationSummary",
    "StatisticalResult",
    "StatisticalWarning",
    "ValidatedABData",
    "ValidatedSample",
    "WarningSeverity",
    "binary_rate_plot_data",
    "continuous_distribution_plot_data",
    "fisher_exact_test",
    "mann_whitney_u_test",
    "permutation_mean_test",
    "simulate_binary_ab",
    "simulate_continuous_ab",
    "student_t_test",
    "summarize_binary_ab",
    "summarize_binary_sample",
    "summarize_continuous_ab",
    "summarize_continuous_sample",
    "two_proportion_z_test",
    "validate_ab_samples",
    "validate_binary_sample",
    "validate_continuous_sample",
    "welch_t_test",
]

__version__ = "0.1.0"
