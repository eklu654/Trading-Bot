# Dynamic Leveraged ETF / Regime Allocation Research

**Status:** New research direction — 2026-10-02  
**Starting account:** $5,000  
**Purpose:** Determine whether dynamic selection among 1x, 2x, 3x and cash can improve risk-adjusted ETF performance without introducing avoidable overfitting.

## Research question

The project should not assume that 3x leverage is universally superior to 2x, or that cash is universally superior during a 200-DMA exit.

The primary hypothesis is:

> A regime-aware system that selects leverage level, ETF/sector exposure and position size may retain a meaningful portion of leveraged upside while reducing drawdown and volatility relative to a static 3x portfolio.

The null hypothesis is that the additional complexity does not produce a persistent improvement after costs, execution assumptions and untouched chronological validation.

## Why this direction is justified

Leveraged ETFs reset daily, so long-horizon results depend on the path of underlying returns and volatility rather than simply multiplying the underlying's cumulative return. Recent academic work documents a particularly clear 2022–2023 example: the S&P 500 rose over the period while corresponding 2x and 3x S&P leveraged ETFs had substantially negative returns; roughly two-thirds of the gap was attributed to volatility/compounding effects, with the remainder associated with timing/covariance effects.

This does **not** imply that leveraged ETFs should be avoided. Earlier research has found that leveraged ETFs can be useful in aggressive portfolios and that their behavior depends materially on return and volatility conditions. The project therefore treats leverage as a variable to manage, not a permanent exposure.

## Proposed exposure ladder

The research universe should conceptually support four risk gears:

1. **0x — cash**
2. **1x — unleveraged underlying/sector exposure**
3. **2x — leveraged exposure**
4. **3x — leveraged exposure**

The exact ETF mapping is a data/availability question and must be frozen before each experiment. The model must not substitute a different instrument simply because it has a better historical result.

## Decision layers

The proposed architecture has five separate layers.

### 1. Market regime

Inputs may include:

- broad-market price versus moving averages;
- moving-average slope;
- distance from moving average;
- realized volatility;
- VIX level;
- VIX trend;
- volatility percentile;
- market breadth;
- momentum;
- credit/risk proxies when reliable historical data are available.

The 200-DMA remains an important candidate feature, not an unconditional master switch.

### 2. Leverage selection

The model chooses among the permitted exposure gears.

Example hypothesis classes:

- strong trend + controlled volatility → permit 3x;
- positive trend + moderate/deteriorating volatility → favor 2x;
- mixed trend → 1x or reduced exposure;
- negative trend → cash/defensive state.

These are candidate states, not frozen rules.

### 3. Relative ETF selection

Within an eligible risk state, compare candidate underlyings using predeclared features such as:

- medium/long-term momentum;
- trend strength;
- relative strength;
- volatility;
- drawdown;
- breadth/participation where applicable.

The system should be capable of discovering that different sectors are preferable in different regimes rather than permanently allocating to TQQQ/SPXL/SOXL.

### 4. Position sizing

Sizing should be constrained independently of the model's ranking.

Hard limits should include:

- maximum single-ETF allocation;
- maximum common-underlying/sector exposure;
- maximum effective portfolio leverage;
- liquidity/turnover limits;
- cash minimum where required.

### 5. Deterministic risk controller

The AI/model cannot override:

- hard position limits;
- hard portfolio leverage limits;
- data-quality failures;
- execution safeguards;
- broker/account constraints;
- emergency controls.

## Candidate experiment ladder

Run experiments in increasing complexity.

### E0 — Existing ETF-001 baseline

Static TQQQ/SPXL/SOXL allocation with the currently validated trend framework.

### E1 — 2x versus 3x

Compare otherwise equivalent 1x/2x/3x exposure under the same trend rule.

### E2 — Dynamic leverage only

Hold the ETF universe fixed but permit 1x/2x/3x/cash selection from market-regime features.

### E3 — Dynamic ETF selection

Allow the regime model to select both leverage and the eligible ETF/sector.

### E4 — Dynamic sizing

Add constrained position sizing.

### E5 — ML/AI selector

Only after deterministic versions establish a benchmark. The ML model must compete against the simpler rules rather than replace them automatically.

## Chronological validation

The existing ETF-001 holdout discipline remains authoritative.

No candidate may use final holdout performance for feature selection, threshold selection, model selection or hyperparameter tuning.

Each new experiment should preserve:

- chronological train/validation/holdout separation;
- signal-to-return one-session shift;
- fixed candidate grids declared before evaluation;
- parameter-neighborhood robustness;
- transaction-cost sensitivity;
- turnover reporting;
- exposure reporting.

For ML, walk-forward training is required. Any feature requiring future observations is prohibited.

## Stress-period reporting

Every promoted candidate must report behavior separately for major historical environments, including:

- 2008 financial crisis;
- 2011 debt/European stress;
- 2015–2016 correction;
- February 2018 volatility shock;
- October–December 2018 deterioration;
- 2020 COVID crash/recovery;
- 2022 rate-hike bear market;
- 2023–2024 recovery;
- most recent available period.

The February 2018 episode is particularly important because the S&P 500's February decline did not rupture the 200-day/12-month trend measures, while the later October decline caused materially greater technical damage. This supports testing volatility shocks separately from sustained trend deterioration rather than treating every volatility spike as equivalent.

## Evaluation metrics

Primary metrics:

- CAGR;
- Sharpe;
- Sortino;
- maximum drawdown;
- Calmar;
- downside deviation;
- worst day;
- worst month;
- longest recovery;
- time under water.

Secondary metrics:

- turnover;
- number of regime changes;
- time in each leverage state;
- average and maximum effective leverage;
- concentration;
- transaction costs;
- slippage sensitivity;
- percentage of profitable months;
- performance by regime;
- performance by stress period.

The project-level performance hurdle is substantial absolute return relative to SPY, not merely a small improvement in risk-adjusted statistics. Every candidate must therefore report CAGR, calendar-year excess return, percentage of years beating SPY, and rolling excess CAGR alongside drawdown and risk metrics. Risk-adjusted metrics determine whether the return profile is survivable; they do not substitute for the project's absolute-return objective.

## Anti-overfitting rules

The project must not:

- select an ETF because it had the highest historical return;
- tune VIX thresholds against the final holdout;
- add indicators after seeing holdout results;
- test hundreds of arbitrary ETF combinations and report only the winner;
- let an AI model optimize directly on the complete historical sample;
- infer that a more complicated model is better merely because its in-sample result is higher.

Model complexity must earn its place by improving unseen-data performance and robustness.

## Cash is a real competitor

Cash must remain an explicit candidate, not merely the default when no ETF is selected.

For every risk-off episode, compare:

- cash;
- 1x exposure;
- 2x exposure;
- alternative 3x exposure;
- dynamic partial exposure.

The question is not whether cash has the highest return during a recovery. The question is whether avoiding enough downside improves the portfolio's long-run risk-adjusted outcome after accounting for the cost of being out of the market.

## Current conclusion

The current deterministic result does not justify promoting dynamic leverage yet: it has not demonstrated the required combination of substantial absolute-return improvement over SPY and robust drawdown behavior.

It **does** justify moving the research to dynamic ETF-family selection. The deterministic E2 experiment now tests whether choosing among SPY/QQQ/SOXX families can create a larger return edge without simply increasing static leverage.

The AI selector remains the eventual target. It should only be promoted after deterministic family selection and sizing controls establish a credible baseline, and only if walk-forward testing shows a meaningful incremental return advantage rather than a cosmetic risk-metric improvement.
