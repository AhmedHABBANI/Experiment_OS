# ExperimentOS Statistics

`experiment-os-stats` is the framework-independent statistical engine used by
ExperimentOS.

## Responsibilities

The package contains:

- input-data validation;
- binary and continuous descriptive statistics;
- experiment simulation;
- frequentist hypothesis tests;
- effect-size calculations;
- bootstrap and permutation methods;
- deterministic statistical interpretation;
- report-ready result structures.

## Architectural rule

This package must not depend on:

- FastAPI;
- React;
- HTTP concepts;
- frontend components;
- database systems.

It should be usable directly from Python:

```python
from experiment_os_stats import StatisticalResult