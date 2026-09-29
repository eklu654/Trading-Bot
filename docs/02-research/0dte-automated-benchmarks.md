# 0DTE 0DTESPX automated benchmark workflow

**Status:** Active research infrastructure — 2026-09-29

The 0DTE benchmark runners use the 0DTESPX API session login endpoint. The
credentials are never written to the repository and the session token is never
saved to disk or printed.

## One-time GitHub setup

Add these two **GitHub Actions secrets** to the `Trading-Bot` repository:

- `ODTESPX_EMAIL`
- `ODTESPX_PASSWORD`

The workflow reads them only through GitHub's `secrets.*` context.

Do not put either value in source files, workflow YAML, JSON results, issues,
or commit messages.

## Running a benchmark

Open the repository's **Actions** tab and run **0DTE 0DTESPX Benchmark** with
**Run workflow**. Select exactly one frozen benchmark:

- `put` — original three put-credit-spread configurations
- `call` — mirrored call-credit-spread configurations
- `iron-condor` — three symmetric iron-condor configurations
- `timing-matrix` — 45-cell management timing matrix

The workflow uploads the sanitized JSON as a GitHub Actions artifact. No JSON
upload to ChatGPT is required for future runs; the artifact can be retrieved
from the workflow run when analysis needs it.

## Local use

The same scripts still work interactively:

    python tools/0dte/run_free_benchmark.py

For non-interactive local runs, set `ODTESPX_EMAIL` and `ODTESPX_PASSWORD`
in the local environment. Do not commit a `.env` file containing credentials.

## Research-use constraint

0DTESPX states that historical market-data reads are metered and that bulk
extraction of its historical archive is not permitted. These benchmark
workflows therefore call the platform's own strategy-preview/backtest engine
rather than downloading the historical archive. They are manual/on-demand
workflows, not a scheduled archive copier.

The 45-cell timing matrix is intentionally frozen. Its results are research
evidence, not an automatic strategy-selection or deployment decision.
