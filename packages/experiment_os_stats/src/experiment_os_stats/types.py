"""Shared enumerations used by the ExperimentOS statistical engine."""

from enum import StrEnum


class MetricType(StrEnum):
    """Families of metrics supported by ExperimentOS."""

    BINARY = "binary"
    CONTINUOUS = "continuous"


class Alternative(StrEnum):
    """Alternative hypotheses supported by statistical tests."""

    TWO_SIDED = "two-sided"
    GREATER = "greater"
    LESS = "less"


class DataSource(StrEnum):
    """Possible origins of an analyzed dataset."""

    SIMULATION = "simulation"
    CSV_IMPORT = "csv_import"


class WarningSeverity(StrEnum):
    """Severity levels assigned to statistical warnings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class MissingValuePolicy(StrEnum):
    """Strategies for handling missing observations."""

    DROP = "drop"
    RAISE = "raise"
