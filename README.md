# ExperimentOS

ExperimentOS is a local full-stack platform for simulating, importing,
analyzing and explaining frequentist A/B experiments.

The project combines:

- a framework-independent Python statistical library;
- a FastAPI backend;
- a React frontend;
- interactive statistical visualizations;
- deterministic result interpretation;
- reproducible execution with Docker Compose.

## Current status

ExperimentOS is under incremental development.

The current milestone includes the statistical library, simulation endpoints
and a minimal React simulation workspace.

## Local run

Run the full local stack:

```bash
docker compose up --build
```

Then open:

- frontend: `http://127.0.0.1:5175`
- backend health: `http://127.0.0.1:8000/api/v1/health`

Python checks are currently run through Docker because the local `.venv`
references a missing Python 3.12 executable:

```bash
docker run --rm -v ${PWD}:/src -w /src python:3.12-slim sh -c "pip install -q -e packages/experiment_os_stats[dev] fastapi httpx && pytest"
```

Frontend checks:

```bash
cd frontend
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

## Planned capabilities

- binary and continuous A/B metrics;
- experiment simulation;
- CSV import and manual column mapping;
- descriptive statistics;
- two-proportion z-test;
- Fisher's exact test;
- Student's t-test;
- Welch's t-test;
- Mann–Whitney U test;
- permutation testing;
- bootstrap confidence intervals;
- JSON, CSV and PDF exports.

## Architecture

```text
Python statistical library
        ↓
FastAPI backend
        ↓
React frontend
```

The statistical library must remain independent from FastAPI and React.

Project documentation
CODEX.md
specs/cahier-des-charges.md
specs/repository-architecture.yaml
specs/roadmap.md
specs/STATUS.md
